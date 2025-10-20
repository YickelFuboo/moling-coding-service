import os
import asyncio
import json
from typing import Optional, Dict, Any, List, Union, AsyncGenerator
from semantic_kernel import Kernel, KernelBuilder
from semantic_kernel.plugin_definition import kernel_function
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.azure_open_ai import AzureOpenAIChatCompletion
from semantic_kernel.connectors.ai.anthropic import AnthropicChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents import PromptExecutionSettings, FunctionChoiceBehavior
from app.utils.logger import logger
from app.utils.common import get_project_base_directory


# 保存全局配置
llm_config = {}

class SemanticKernelService:
    """Semantic Kernel服务类 - 提供AI内核的创建、配置和执行能力"""
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None, api_key: Optional[str] = None, **kwargs):

        # 加载全局配置
        self.config_path = os.path.join(get_project_base_directory(), "app", "config", "chat_models.json")
        if not llm_config:
            self._load_config()
            self._config = llm_config

        # 配置模型信息
        if not provider or not model:
            self.provider, self.model = self._get_default_model()
        else:
            self.provider = provider
            self.model = model

        model_para = self._get_model_para(self.provider, self.model)
        if not model_para["success"]:
            raise ValueError(f"获取模型参数失败: {model_para.get('error', '未知错误')}")
        
        self.api_key = api_key or model_para["api_key"]
        self.base_url = model_para["base_url"]
        self.kwargs = kwargs

        # 获取模型默认配置参数
        for key, value in model_para["model_params"].items():
            if key not in self.kwargs:
                self.kwargs[key] = value

        # 创建kernel实例
        self.kernel = self._create_kernel()
    
    def _load_config(self):
        """加载LLM配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"聊天模型配置文件未找到: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"聊天模型配置文件格式错误: {e}")
    
    def _get_default_model(self) -> tuple[str, str]:
        """
        获取默认模型
        
        Returns:
            tuple[str, str]: (供应商名字, 模型名字)
        """
        default_config = self._config.get("default", {})
        
        provider = default_config.get("provider", "")
        model = default_config.get("model", "")

        return provider, model
    
    def _get_model_para(self, provider: str, model: str) -> Dict[str, Any]:
        """
        获取模型参数（合并provider和model配置）
        
        Args:
            provider: 供应商名称
            model: 模型名称
            
        Returns:
            Dict[str, Any]: 包含以下字段的字典：
            {
                "success": bool,  # 成功标志
                "api_key": str,   # API密钥
                "base_url": str,  # 基础URL
                "model_params": Dict[str, Any]  # 模型参数集
            }
        """
        try:
            # 直接获取配置
            models = self._config.get("models", {})
            if provider not in models:
                raise ValueError(f"不支持的模型供应商: {provider}")
            
            provider_config = models[provider]
            
            # 检查provider是否有效
            if provider_config.get("is_valid", 0) != 1:
                raise ValueError(f"供应商 {provider} 未启用")
            
            instances = provider_config.get("instances", {})
            if model not in instances:
                raise ValueError(f"供应商 {provider} 不支持模型: {model}")
            
            model_config = instances[model]
            
            return {
                "success": True,
                "api_key": provider_config.get("api_key", ""),
                "base_url": provider_config.get("base_url", ""),
                "model_params": model_config
            }
        except Exception as e:
            return {
                "success": False,
                "api_key": "",
                "base_url": "",
                "model_params": {},
                "error": str(e)
            }

    def _create_kernel(self) -> Kernel:
        """创建和配置AI内核实例"""
        try:
            # 创建内核构建器
            kernel_builder = KernelBuilder()
            
            # 配置AI模型服务 - 使用现代API
            self._configure_ai_service_with_builder(
                kernel_builder, 
                self.provider, 
                self.model, 
                self.base_url, 
                self.api_key
            )
            
            # 构建内核
            kernel = kernel_builder.build()
            
            logger.info(f"创建AI内核成功: {self.model}")
            return kernel
            
        except Exception as e:
            logger.error(f"创建AI内核失败: {e}")
            raise
    
    
    def _configure_ai_service_with_builder(self, kernel_builder: KernelBuilder, provider: str, model: str, base_url: str, api_key: str):
        """使用KernelBuilder配置AI服务"""
        try:
            provider_lower = provider.lower()
            
            if provider_lower in ["openai", "deepseek", "silicon", "siliconflow", "qwen"]:
                # 配置OpenAI兼容服务
                chat_service = OpenAIChatCompletion(
                    service_id=provider_lower,
                    ai_model_id=model,
                    api_key=api_key,
                    endpoint=base_url
                )
                kernel_builder.add_service(chat_service)
                
            elif provider_lower == "azure":
                # 配置Azure OpenAI服务
                chat_service = AzureOpenAIChatCompletion(
                    service_id="azure_openai",
                    ai_model_id=model,
                    api_key=api_key,
                    endpoint=base_url
                )
                kernel_builder.add_service(chat_service)
                
            elif provider_lower in ["anthropic", "claude"]:
                # 配置Anthropic服务
                chat_service = AnthropicChatCompletion(
                    service_id="anthropic",
                    ai_model_id=model,
                    api_key=api_key,
                    endpoint=base_url
                )
                kernel_builder.add_service(chat_service)
                
            else:
                raise ValueError(f"不支持的AI服务提供商: {provider}")
                
        except Exception as e:
            logger.error(f"配置AI服务失败: {e}")
            raise

    
    async def add_semantic_functions(self, path: str) -> bool:
        """
        添加Semantic Functions到Kernel
        自动判断：如果目录包含config.json则直接加载，否则扫描子目录
        
        Semantic Functions目录标准格式：
        plugin_directory/
        ├── config.json          # 函数配置文件
        └── skprompt.txt         # 提示词模板文件
        
        Args:
            path: 相对于项目根目录的插件路径
            
        Returns:
            bool: 是否成功加载
        """
        try:
            if not self.kernel:
                raise ValueError("Kernel未初始化，请先调用initialize()方法")
            
            # 将相对路径转换为绝对路径
            plugin_directory = os.path.join(get_project_base_directory(), path)            
            if not os.path.exists(plugin_directory):
                logger.error(f"插件目录不存在: {plugin_directory}")
                return False
            
            if os.path.exists(os.path.join(plugin_directory, "config.json")):
                # 直接加载当前目录的插件
                plugin_name = os.path.basename(plugin_directory)
                
                self.kernel.add_plugin(
                    plugin_name=plugin_name,
                    plugin_directory=plugin_directory
                )
                
                logger.info(f"成功从目录加载插件: {plugin_name} from {plugin_directory}")
                return True
            
            else:
                # 扫描子目录
                success_count = 0                
                for item in os.listdir(plugin_directory):
                    item_path = os.path.join(plugin_directory, item)
                    
                    # 只处理目录
                    if not os.path.isdir(item_path):
                        continue
                    
                    # 检查子目录是否包含config.json文件（Semantic Kernel插件标准格式）
                    if not os.path.exists(os.path.join(item_path, "config.json")):
                        continue
                    
                    # 尝试加载插件（使用子目录名作为插件名）
                    try:
                        self.kernel.add_plugin(
                            plugin_name=item,
                            plugin_directory=item_path
                        )
                        success_count += 1
                        logger.info(f"成功加载插件: {item}")
                        
                    except Exception as e:
                        logger.error(f"加载插件 {item} 时发生错误: {e}")
                
                logger.info(f"插件加载完成: {success_count} 个插件加载成功")
                return success_count > 0
        
        except Exception as e:
            logger.error(f"从目录加载插件失败: {e}")
            return False
    
    async def add_native_functions(self, function_instance: Any, function_name: Optional[str] = None) -> bool:
        """
        添加Native Functions到Kernel
        
        Native Functions是使用@kernel_function装饰器标记的Python函数
        
        Args:
            function_instance: Function对象实例
            function_name: 函数名称（可选，如果不提供则使用类名）
            
        Returns:
            bool: 是否成功添加
        """
        try:
            if not self.kernel:
                raise ValueError("Kernel未初始化，请先调用initialize()方法")
                
            if function_name is None:
                function_name = function_instance.__class__.__name__
            
            # 添加函数到Kernel
            self.kernel.add_function(
                plugin_name="custom_functions",
                function_name=function_name,
                function=function_instance
            )
            
            logger.info(f"成功添加函数到Kernel: {function_name}")
            return True
            
        except Exception as e:
            logger.error(f"添加函数到Kernel失败: {e}")
            return False
    
    
    async def invoke_prompt(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, auto_calls: Optional[bool] = True, **kwargs) -> str:
        """
        执行Prompt调用（非流式）
        
        Args:
            messages: 用户消息
            system_prompt: 系统提示词（可选）
            auto_calls: 是否自动调用工具（默认True）
            **kwargs: 其他参数（temperature, max_tokens, history, arguments等）
            
        Returns:
            str: 完整响应内容
        """
        try:

            history = ChatHistory()

            if system_prompt:
                history.add_system_message(system_prompt)

            for message in messages:
                if message["role"] == "user":
                    history.add_user_message(message["content"])
                elif message["role"] == "assistant":
                    history.add_assistant_message(message["content"])

            # 执行调用
            if auto_calls:
                result = await self.kernel.invoke_prompt(
                    prompt="{{history}}",
                    arguments=KernelArguments(
                        settings=PromptExecutionSettings(
                            function_choice_behavior=FunctionChoiceBehavior.Auto()
                        ),
                        history=history,
                    ),
                    **kwargs
                )
            else:
                result = await self.kernel.invoke_prompt(
                    prompt="{{history}}",
                    arguments=KernelArguments(
                        history=history,
                    ),
                    **kwargs
                )

            # 提取内容
            if hasattr(result, 'content') and result.content:
                content = str(result.content)
            else:
                content = str(result)
            
            logger.info("Prompt调用执行完成")
            return content
            
        except Exception as e:
            logger.error(f"执行Prompt调用失败: {e}")
            raise
    

    async def invoke_prompt_stream(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, auto_calls: Optional[bool] = True, **kwargs) -> AsyncGenerator[str, None]:
        """
        执行Prompt流式调用
        
        Args:
            messages: 用户消息
            system_prompt: 系统提示词（可选）
            auto_calls: 是否自动调用工具（默认True）
            **kwargs: 其他参数（temperature, max_tokens, history, arguments等）
            
        Yields:
            str: 流式响应内容
        """
        try:
            logger.info(f"开始执行Prompt流式调用: {len(messages)}条消息")
            
            history = ChatHistory()

            if system_prompt:
                history.add_system_message(system_prompt)

            for message in messages:
                if message["role"] == "user":
                    history.add_user_message(message["content"])
                elif message["role"] == "assistant":
                    history.add_assistant_message(message["content"])

            # 执行流式调用
            if auto_calls:
                async for chunk in self.kernel.invoke_prompt_stream(
                    prompt="{{history}}",
                    arguments=KernelArguments(
                        settings=PromptExecutionSettings(
                            function_choice_behavior=FunctionChoiceBehavior.Auto()
                        ),
                        history=history,
                    ),
                    **kwargs
                ):
                    if hasattr(chunk, "content") and chunk.content:
                        yield str(chunk.content)
                    elif isinstance(chunk, list):
                        for m in chunk:
                            if hasattr(m, "content") and m.content:
                                yield str(m.content)
                    else:
                        yield str(chunk)
            else:
                async for chunk in self.kernel.invoke_prompt_stream(
                    prompt="{{history}}",
                    arguments=KernelArguments(
                        history=history,
                    ),
                    **kwargs
                ):
                    if hasattr(chunk, "content") and chunk.content:
                        yield str(chunk.content)
                    elif isinstance(chunk, list):
                        for m in chunk:
                            if hasattr(m, "content") and m.content:
                                yield str(m.content)
                    else:
                        yield str(chunk)
            
            logger.info("Prompt流式调用执行完成")
            
        except Exception as e:
            logger.error(f"执行Prompt流式调用失败: {e}")
            raise
    
    
    async def invoke_plugin_function(self, plugin_name: str, function_name: str, **kwargs) -> str:
        """
        执行指定插件的函数
        
        Args:
            plugin_name: 插件名称
            function_name: 函数名称
            **kwargs: 函数参数
            
        Returns:
            str: 执行结果
        """
        try:
            logger.info(f"开始执行插件函数: {plugin_name}.{function_name}")
            
            # 获取插件和函数
            plugin = self.kernel.get_plugin(plugin_name)
            if not plugin:
                raise ValueError(f"插件 {plugin_name} 不存在")
            
            function = plugin.get_function(function_name)
            if not function:
                raise ValueError(f"函数 {function_name} 在插件 {plugin_name} 中不存在")
            
            # 执行函数
            result = await self.kernel.invoke(
                function=function,
                arguments=KernelArguments(
                                PromptExecutionSettings(
                                    function_choice_behavior=FunctionChoiceBehavior.Auto()
                                ),
                            ),
                kwargs=kwargs
            )
            
            # 提取内容
            generated = str(result) if result else ""
            
            logger.info(f"插件函数执行完成: {plugin_name}.{function_name}")
            return generated
            
        except Exception as e:
            logger.error(f"执行插件函数失败: {e}")
            raise
    
    
    async def invoke_plugin_function_stream(self, plugin_name: str, function_name: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        执行指定插件的函数（流式）
        
        Args:
            plugin_name: 插件名称
            function_name: 函数名称
            **kwargs: 函数参数
            
        Yields:
            str: 流式响应内容
        """
        try:
            logger.info(f"开始执行插件函数流式调用: {plugin_name}.{function_name}")
            
            # 执行流式调用
            async for chunk in self.kernel.invoke_function_stream(
                plugin_name=plugin_name,
                function_name=function_name,
                **kwargs
            ):
                if hasattr(chunk, "content") and chunk.content:
                    yield str(chunk.content)
                elif isinstance(chunk, list):
                    for m in chunk:
                        if hasattr(m, "content") and m.content:
                            yield str(m.content)
                else:
                    yield str(chunk)
            
            logger.info(f"插件函数流式调用执行完成: {plugin_name}.{function_name}")
            
        except Exception as e:
            logger.error(f"执行插件函数流式调用失败: {e}")
            raise
    
    
    

