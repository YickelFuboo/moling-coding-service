import uuid
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.domains.code_wiki.models.wiki_document import WikiDocument, WikiGenStatus
from app.domains.repo_mgmt.models.repository import RepoRecord, ProcessingStatus
from app.domains.code_wiki.services.document_gen_service import DocumentGenService


class WikiDocumentService:
    """Wiki服务"""
    
    @staticmethod
    async def create_wiki_document(
        session: AsyncSession,
        repo_id: str
    ) -> WikiDocument:
        """创建wiki文档"""
        try:
            # 获取仓库信息
            result = await session.execute(
                select(RepoRecord).where(RepoRecord.id == repo_id)
            )
            repo_record = result.scalar_one_or_none()
            if not repo_record:
                raise ValueError(f"仓库 {repo_id} 不存在")
            
            # 生成文档ID
            doc_id = f"wiki_{repo_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # 创建wiki文档
            wiki_document = WikiDocument(
                id=doc_id,
                repo_id=repo_id,
                path=repo_record.local_path, 
                description=repo_record.repo_description or "", 
                status=WikiGenStatus.Pending,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(wiki_document)
            await session.commit()
            await session.refresh(wiki_document)

            # 启动wiki生成
            await WikiDocumentService.update_wiki_document_status(session, doc_id, WikiGenStatus.Processing)
            await DocumentGenService.generate_document(session, wiki_document.id)
            await WikiDocumentService.update_wiki_document_status(session, doc_id, WikiGenStatus.Completed)
            
            
            logging.info(f"创建wiki文档: {wiki_document.id}")
            return wiki_document
            
        except Exception as e:
            logging.error(f"创建wiki文档失败: {e}")
            raise
    
    @staticmethod
    async def get_wiki_document(
        session: AsyncSession,
        doc_id: str
    ) -> Optional[WikiDocument]:
        """获取wiki文档"""
        try:
            result = await session.execute(
                select(WikiDocument).where(WikiDocument.id == doc_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logging.error(f"获取wiki文档失败: {e}")
            return None
    
    @staticmethod
    async def update_wiki_document_status(
        session: AsyncSession,
        doc_id: str,
        status: WikiGenStatus,
        content: str = None,
        error_message: str = None
    ) -> bool:
        """更新wiki文档状态"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if content is not None:
                update_data["content"] = content
            if error_message is not None:
                update_data["error_message"] = error_message
            
            result = await session.execute(
                update(WikiDocument)
                .where(WikiDocument.id == doc_id)
                .values(**update_data)
            )
            
            await session.commit()
            return result.rowcount > 0
            
        except Exception as e:
            logging.error(f"更新wiki文档状态失败: {e}")
            return False
    
    @staticmethod
    async def delete_wiki_document(
        session: AsyncSession,
        doc_id: str
    ) -> bool:
        """删除wiki文档"""
        try:
            result = await session.execute(
                delete(WikiDocument)
                .where(WikiDocument.id == doc_id)
            )
            
            await session.commit()
            return result.rowcount > 0
            
        except Exception as e:
            logging.error(f"删除wiki文档失败: {e}")
            return False
