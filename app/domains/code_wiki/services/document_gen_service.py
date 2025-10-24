import uuid
import re
import json
import asyncio
import logging
from typing import List
from datetime import datetime
from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, insert
from git import Repo
from app.config.settings import settings
from app.domains.repo_mgmt.services.local_repo_service import LocalRepoService
from app.domains.code_wiki.models.wiki_document import WikiDocument
from app.domains.ai_kernel.kernel_factory import KernelFactory
from app.domains.repo_mgmt.services.repo_mgmt_service import RepoMgmtService
from semantic_kernel.functions import KernelArguments
from semantic_kernel.kernel import PromptTemplateConfig


class DocumentGenService:
    """文档生成服务"""

    @staticmethod
    async def generate_document(session: AsyncSession, document_id: str):
        """生成文档"""
        try:
            from app.domains.code_wiki.services.wiki_document_service import WikiDocumentService
            document = await WikiDocumentService.get_wiki_document(session, document_id)
            if not document:
                raise ValueError(f"文档 {document_id} 不存在")

            from app.domains.repo_mgmt.services.repo_mgmt_service import RepoMgmtService
            repo_record = await RepoMgmtService.get_repository_by_id(session, document.repo_id)
            if not repo_record:
                raise ValueError(f"仓库 {document.repo_id} 不存在")

            # 获取仓库的本地路径，用于文件系统操作
            git_local_path = document.path
            git_repository = repo_record.repo_url.replace(".git", "")           
                                                      
            # 步骤1: 读取或生成README
            readme = await DocumentGenService.generate_readme(document, git_local_path, session)
            
            # 步骤2: 读取并且生成目录结构
            catalogue = await DocumentGenService.generate_catalogue(warehouse, git_local_path, readme, db)
            
            # 步骤3: 读取或生成项目类别
            classify = await DocumentGenService.generate_classify(warehouse, git_local_path, catalogue, readme, db)
            
            # 步骤4: 生成知识图谱
            minmap = await MiniMapService.generate_mini_map(warehouse, git_local_path, catalogue, db)
            
            # 步骤5: 生成项目概述
            overview = await DocumentGenService.generate_overview(warehouse, document, catalogue, 
                                git_repository, readme, classify, db)
            
            # 步骤6: 生成目录结构
            document_catalogs = await RepoWikiContentService.generate_wiki_catalogs_structure(warehouse, document, 
                                    git_local_path, git_repository, catalogue, classify, db)
            
            # 步骤7: 生成目录结构中的文档内容
            await RepoWikiContentService.generate_catalog_documents_content(document_catalogs, catalogue, 
                                            git_repository, warehouse, git_local_path, classify, db)
            
            # 步骤8: 生成更新日志 (仅Git仓库)
            if warehouse.type and warehouse.type.lower() == "git":
                await _generate_update_log(warehouse, document.git_path, readme, git_repository, db)
            
            # 更新文档最后更新时间
            await db.execute(
                update(Document)
                .where(Document.id == document.id)
                .values(
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            logging.info(f"AI文档处理完成: {document.id}")
            
        except Exception as e:
            logging.error(f"AI文档处理失败: {document.id}, 错误: {e}")
            
            # 更新文档最后更新时间
            await db.execute(
                update(Document)
                .where(Document.id == document.id)
                .values(
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            # 重新抛出异常，触发Celery重试
            raise
        
    @staticmethod
    async def generate_readme(document: WikiDocument, path: str, session: AsyncSession) -> str:
        """步骤1: 生成README文档
        1) 优先读取本地 README（多种扩展名）
        2) 若不存在，则获取目录结构并尝试通过语义插件 CodeAnalysis/GenerateReadme 生成
        3) 解析 <readme> 标签内容；若失败则直接使用原始文本
        4) 返回生成/读取的 README 文本（本项目模型暂无 readme 字段，暂不落库）
        """
        try:
            # 获取git仓信息
            RepoRecord = RepoMgmtService.get_repository_by_id(session, document.repo_id)
            if not RepoRecord:
                raise ValueError(f"仓库 {document.repo_id} 不存在")
            git_repository = RepoRecord.repo_url.replace(".git", "")
            branch = RepoRecord.repo_branch


            # 1. 优先读取现有 README
            readme: str = await LocalRepoService.get_readme_file(path)

            # 2. 若无本地 README，则使用AI生成
            if not readme:
                # 2.1 获取目录结构（紧凑格式）
                try:
                    catalogue = await LocalRepoService.get_catalogue(path)
                except Exception as e:
                    logging.warning(f"获取目录结构失败，将使用空目录结构。错误: {e}")
                    catalogue = ""

                # 2.2 创建 AI 内核（加载 CodeAnalysis 语义插件 + FileFunction 原生插件）
                try:
                    kernel_factory = KernelFactory()
                    # 加载语义插件以便可用 CodeAnalysis/GenerateReadme
                    kernel = await kernel_factory.get_kernel(git_local_path=path, is_code_analysis=True)
                except Exception as e:
                    logging.error(f"创建AI内核失败，将回退到基础README。错误: {e}")
                    kernel = None

                # 2.3 调用生成 README 的语义插件
                generated = None
                if kernel is not None:
                    try:
                        generate_fn = kernel.get_plugin("CodeAnalysis").get_function("GenerateReadme")
                        if generate_fn is not None:
                            result = await kernel.invoke(
                                function=generate_fn,
                                arguments=KernelArguments(
                                    PromptExecutionSettings(
                                        function_choice_behavior=FunctionChoiceBehavior.Auto()
                                    ),
                                ),
                                kwargs={
                                    "catalogue": catalogue or "",
                                    "git_repository": git_repository,
                                    "branch": branch,
                                }
                            )
                            generated = str(result) if result else None
                        else:
                            logging.warning("未发现语义插件 CodeAnalysis/GenerateReadme，跳过AI生成。")
                            generated = None
                    except Exception as e:
                        logging.error(f"调用GenerateReadme插件失败，将回退到基础README。错误: {e}")

                # 2.4 解析 AI 输出
                if generated:
                    match = re.search(r"<readme>(.*?)</readme>", generated, re.DOTALL | re.IGNORECASE)
                    readme = match.group(1) if match else generated

            # 3. 将readme落库
            if readme:
                await db.execute(
                    update(Warehouse)
                    .where(Warehouse.id == warehouse.id)
                    .values(readme=readme)
                )
                await db.commit()
            else:
                # 若数据库中直接存在readme，则使用数据库中的readme
                readme = warehouse.readme

            return readme
        except Exception as e:
            logging.error(f"生成README失败: {e}")
            return ""


    async def _generate_catalogue(warehouse: Warehouse, path: str, readme: str, db: AsyncSession) -> str:
        """步骤2: 生成目录结构
        - 扫描目录统计条目数；小于阈值或未启用智能过滤时，直接构建优化目录结构
        - 否则启用 AI 智能过滤：使用 CodeAnalysis/CodeDirSimplifier 插件，支持重试与解析结果
        - 成功后写入 warehouse.optimized_directory_structure
        """
        try:
            # 获取配置参数
            enable_smart_filter = (getattr(settings, "document", None) and settings.document.enable_smart_filter) is True
            catalogue_format = (getattr(settings, "document", None) and settings.document.catalogue_format) or "compact"

            # 获取目录文件列表
            path_infos = LocalRepoService.get_folders_and_files(path)
            total_items = len(path_infos)

            catalogue = LocalRepoService.get_catalogue_optimized(path, catalogue_format)

            if total_items > 800 and enable_smart_filter:
                # 启动AI智能过滤
                kernel_factory = KernelFactory()
                kernel = await kernel_factory.get_kernel(git_local_path=path, is_code_analysis=True)

                if kernel is not None:
                    result_text = ""
                    max_retries = 5
                    last_exception = None

                    for retry_idx in range(max_retries):
                        try:
                            simplify_fn = kernel.get_plugin("CodeAnalysis").get_function("CodeDirSimplifier")
                            if simplify_fn is not None:
                                stream_chunks = []
                                async for stream_message in kernel.invoke_stream(
                                    function=simplify_fn,
                                    arguments=KernelArguments(
                                        settings=PromptExecutionSettings(
                                            function_choice_behavior=FunctionChoiceBehavior.Auto()
                                        )
                                    ),
                                    kwargs={
                                        "code_files": catalogue,
                                        "readme": readme or ""
                                    }
                                ):
                                    # 兼容多种流式消息类型，尽量抽取文本内容
                                    try:
                                        if hasattr(stream_message, "content") and stream_message.content:
                                            stream_chunks.append(str(stream_message.content))
                                        elif isinstance(stream_message, list):
                                            for m in stream_message:
                                                if hasattr(m, "content") and m.content:
                                                    stream_chunks.append(str(m.content))
                                        else:
                                            stream_chunks.append(str(stream_message))
                                    except Exception:
                                        # 异常时尽量不影响主流程
                                        stream_chunks.append(str(stream_message))
                                result_text = "".join(stream_chunks)
                                last_exception = None
                                break
                            else:
                                logging.warning("未发现语义插件 CodeAnalysis/CodeDirSimplifier，回退为直接构建目录结构。")
                                break
                        except Exception as ex:
                            last_exception = ex
                            logging.error(f"优化目录结构失败，重试第{retry_idx + 1}次：{ex}")
                            await asyncio.sleep(5 * (retry_idx + 1))

                    if last_exception is not None:
                        logger.error(f"优化目录结构失败，已重试{max_retries}次：{last_exception}")

                    # 3.2 解析 AI 输出，或在失败时回退
                    if result_text:
                        # 解析 <response_file>...</response_file>
                        match = re.search(r"<response_file>(.*?)</response_file>", result_text, re.DOTALL | re.IGNORECASE)
                        if match:
                            catalogue = match.group(1)
                        else:
                            # 解析 ```json ... ```
                            json_match = re.search(r"```json(.*?)```", result_text, re.DOTALL | re.IGNORECASE)
                            if json_match:
                                catalogue = json_match.group(1).strip()
                            else:
                                catalogue = result_text

            # 4) 写入数据库
            if catalogue:
                await db.execute(
                    update(Warehouse)
                    .where(Warehouse.id == warehouse.id)
                    .values(optimized_directory_structure=catalogue)
                )
                await db.commit()
            else:
                # 若数据库中直接存在catalogue，则使用数据库中的catalogue
                catalogue = warehouse.optimized_directory_structure

            return catalogue

        except Exception as e:
            logger.error(f"生成目录结构失败: {e}")
            return ""


    async def _generate_classify(warehouse: Warehouse, path: str, catalogue: str, readme: str, db: AsyncSession):
        """步骤3: 生成项目类别"""
        try:
            # 如果数据库中没有项目分类，则使用AI进行分类分析
            classify = warehouse.classify
            if not classify:
                # 启动AI智能过滤
                kernel_factory = KernelFactory()
                kernel = await kernel_factory.get_kernel(git_local_path=path, is_code_analysis=False)

                prompt = await PromptTemplate.get_prompt_template("Warehouse/RepositoryClassification.md")

                stream_chunks = []
                async for stream_message in kernel.invoke_prompt_stream(
                    prompt=prompt,
                    arguments=KernelArguments(                    
                        temperature=0.1,
                        max_tokens=settings.llm.get_default_model().max_context_tokens,
                    ),
                    kwargs={
                        "code_files": catalogue,
                        "readme": readme or ""
                    }
                ):
                    # 兼容多种流式消息类型，尽量抽取文本内容
                    try:
                        if hasattr(stream_message, "content") and stream_message.content:
                            stream_chunks.append(str(stream_message.content))
                        elif isinstance(stream_message, list):
                            for m in stream_message:
                                if hasattr(m, "content") and m.content:
                                    stream_chunks.append(str(m.content))
                        else:
                            stream_chunks.append(str(stream_message))
                    except Exception:
                        # 异常时尽量不影响主流程
                        stream_chunks.append(str(stream_message))

                result_text = "".join(stream_chunks)

                classify = None
                if result_text:
                    match = re.search(r"<classify>(.*?)</classify>", result_text, re.DOTALL | re.IGNORECASE)
                    if match:
                        extracted = match.group(1) or ""
                        extracted = re.sub(r"^\s*classifyName\s*:\s*", "", extracted, flags=re.IGNORECASE).strip()
                        if extracted:
                            try:
                                classify = getattr(ClassifyType, extracted)
                            except AttributeError:
                                pass

            # 将项目分类结果保存到数据库
            await db.execute(
                update(Warehouse)
                .where(Warehouse.id == warehouse.id)
                .values(classify=classify)
            )
            await db.commit()
            
            return classify
        except Exception as e:
            logger.error(f"生成项目类别失败: {e}")
            return None

    async def _generate_overview(warehouse: Warehouse, document: Document, catalogue: str, 
                            git_repository: str, readme: str, classify, db: AsyncSession):
        """步骤5: 生成项目概述"""
        try:
            # 启动AI智能过滤
            kernel_factory = KernelFactory()
            kernel = await kernel_factory.get_kernel(git_local_path=warehouse.local_path, is_code_analysis=True)

            prompt_name = "Overview" + classify
            prompt = await PromptTemplate.get_prompt_template(f"Warehouse/{prompt_name}.md")

            # 流式调用，聚合文本
            stream_chunks: List[str] = []
            async for stream_message in kernel.invoke_prompt_stream(
                prompt=prompt,
                arguments=KernelArguments(
                    settings=PromptExecutionSettings(
                        function_choice_behavior=FunctionChoiceBehavior.Auto()
                    ),
                    max_tokens=settings.llm.get_default_model().max_context_tokens,
                ),
                kwargs={
                    "catalogue": catalogue,
                    "git_repository": (warehouse.repository_url or "").replace(".git", ""),
                    "branch": warehouse.branch or "",
                    "readme": readme
                },
            ):
                try:
                    if hasattr(stream_message, "content") and stream_message.content:
                        stream_chunks.append(str(stream_message.content))
                    elif isinstance(stream_message, list):
                        for m in stream_message:
                            if hasattr(m, "content") and m.content:
                                stream_chunks.append(str(m.content))
                    else:
                        stream_chunks.append(str(stream_message))
                except Exception:
                    # 容错处理，尽量不中断主流程
                    stream_chunks.append(str(stream_message))

            overview_text = "".join(stream_chunks)

            # 删除<thinking>...</thinking>内容
            overview_text = re.sub(r"<blog>(.*?)</blog>", "", overview_text, flags=re.DOTALL | re.IGNORECASE).strip()

            # 清理项目分析标签内容（某些模型会生成不需要的标签）
            project_analysis = re.search(r"<project_analysis>(.*?)</project_analysis>", overview_text, re.DOTALL | re.IGNORECASE)
            if project_analysis:
                overview_text = overview_text.replace(project_analysis.group(1), "")

            # 提取blog标签中的内容（某些模型会包装在blog标签中）
            overview_match = re.search(r"<blog>(.*?)</blog>", overview_text, re.DOTALL | re.IGNORECASE)
            if overview_match:
                # 提取blog标签内的内容
                overview = overview_match.group(1)

            # 删除旧的概述数据
            await db.execute(
                delete(DocumentOverview)
                .where(DocumentOverview.document_id == document.id)
            )
            await db.commit()

            # 保存新的项目概述到数据库
            await db.execute(
                insert(DocumentOverview)
                .values(
                    content=overview,
                    title="",
                    document_id=document.id,
                    id=str(uuid.uuid4())
                )
            )
            await db.commit()

            return overview
        except Exception as e:
            logger.error(f"生成项目概述失败: {e}")
            return ""   


    async def _generate_update_log(warehouse: Warehouse, git_path: str, readme: str, git_repository: str, db: AsyncSession):
        """步骤8: 生成更新日志 (仅Git仓库)"""
        try:
            # 删除旧的提交记录
            await db.execute(
                delete(DocumentCommitRecord).where(DocumentCommitRecord.warehouse_id == warehouse.id)
            )

            # 读取git log
            repo = Repo(git_path)
            logs = repo.commits.order_by(lambda x: x.committer.when).take(20).order_by(lambda x: x.committer.when).to_list()

            commit_message = ""
            for commit in logs:
                commit_message += "提交人：" + commit.committer.name + "\n提交内容\n<message>\n" + commit.message + "<message>"
                commit_message += "\n提交时间：" + commit.committer.when.strftime("%Y-%m-%d %H:%M:%S") + "\n"

            kernel_factory = KernelFactory()
            kernel = await kernel_factory.get_kernel(git_local_path=git_path, is_code_analysis=True)
            # 2.3 调用生成 README 的语义插件
            log_result = None
            if kernel is not None:
                try:
                    generate_fn = kernel.get_plugin("CodeAnalysis").get_function("CommitAnalyze")
                    if generate_fn is not None:
                        result = await kernel.invoke(
                            function=generate_fn,
                            kwargs={
                                "readme": readme,
                                "git_repository": git_repository,
                                "commit_message": commit_message,
                                "branch": warehouse.branch
                            }
                        )
                        log_result = str(result) if result else None
                    else:
                        logger.warning("未发现语义插件 CodeAnalysis/CommitAnalyze，跳过AI生成。")
                        log_result = None
                except Exception as e:
                    logger.error(f"调用CommitAnalyze插件失败，将回退到基础README。错误: {e}")

            if log_result:
                match = re.search(r"<changelog>(.*?)</changelog>", log_result, re.DOTALL | re.IGNORECASE)
                if match:
                    log_result = match.group(1)

            commit_result = CommitResultDto.from_json(log_result)

            record = []
            for item in commit_result:
                record.append(DocumentCommitRecord(
                    warehouse_id=warehouse.id,
                    created_at=datetime.now(),
                    author="",
                    id=str(uuid.uuid4()),
                    commit_message=item.description,
                    title=item.title,
                    last_update=item.date
                ))

            await db.execute(
                delete(DocumentCommitRecord).where(DocumentCommitRecord.warehouse_id == warehouse.id)
            )
            await db.commit()

            await db.execute(insert(DocumentCommitRecord).values(record))
            await db.commit()
            
        except Exception as e:
            logger.error(f"生成更新日志失败: {e}")