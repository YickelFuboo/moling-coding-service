import os
import asyncio
import json
import logging
from typing import Optional
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.azure_open_ai import AzureOpenAIChatCompletion
from semantic_kernel.connectors.ai.anthropic import AnthropicChatCompletion
from semantic_kernel.plugin_definition import kernel_function
from app.config.settings import settings
from app.infrastructure.llm.llms.chat_models.factory import llm_factory
from .functions.file_function import FileFunction
from .functions.code_analyze_function import CodeAnalyzeFunction


class KernelFactory:
    """AI内核工厂类"""
    
    def __init__(self):
        self.kernel_cache = {}
    
    async def get_kernel(self, git_local_path: str,  
                        is_code_analysis: bool = True) -> Kernel:
        """创建和配置AI内核实例"""
        try:
            # 获取模型配置
            model_provider, model_name = llm_factory.get_default_model()
            model_config = llm_factory.get_model_info_by_name(model_name)
            if not model_config:
                logging.error("没有可用的模型配置")
                raise Exception("没有可用的模型配置")
            base_url = model_config.get('provider_info').get('base_url')
            api_key = model_config.get('provider_info').get('api_key')
            logging.info(f"模型配置: provider:{model_provider}, model:{model_name}, base_url:{base_url}, api_key:{api_key}")
            
            # 创建缓存键
            cache_key = f"{base_url}_{api_key}_{git_local_path}_{model_name}_{is_code_analysis}"
            
            # 检查缓存
            if cache_key in self.kernel_cache:
                return self.kernel_cache[cache_key]
            
            # 创建内核
            kernel = Kernel()
            
            # 配置AI模型服务
            await self._configure_ai_service_with_model(kernel, model_provider, model_name, base_url, api_key)
            
            # 配置代码分析插件
            if is_code_analysis:
                # 从目录加载语义插件（config.json + skprompt.txt）
                plugins_path = os.path.join(os.getcwd(), "plugins", "CodeAnalysis")
                if os.path.exists(plugins_path):
                    try:
                        kernel.add_plugin(
                            plugin_name="CodeAnalysis",
                            plugin_instance=kernel.get_plugin("CodeAnalysis")
                        )
                        logging.info(f"成功加载语义插件: {plugins_path}")
                    except Exception as e:
                        logging.error(f"加载语义插件失败: {e}")
                else:
                    logging.warning(f"代码分析插件目录不存在: {plugins_path}")
            
            # 配置文件操作插件
            try:
                file_function = FileFunction(git_local_path)
                kernel.add_plugin(
                    plugin_name="FileFunction",
                    plugin_instance=file_function
                )
                logging.info("加载文件操作插件")
            except Exception as e:
                logging.error(f"配置文件操作插件失败: {e}")
            
            # 配置代码依赖分析插件
            if settings.enable_code_dependency_analysis:
                try:
                    code_analyze_function = CodeAnalyzeFunction(git_local_path)
                    kernel.add_plugin(
                        plugin_name="CodeAnalyzeFunction",
                        plugin_instance=code_analyze_function
                    )
                    logging.info("加载代码依赖分析插件")
                except Exception as e:
                    logging.error(f"配置代码依赖分析插件失败: {e}")
            
            # 缓存内核
            self.kernel_cache[cache_key] = kernel
            
            logging.info(f"创建AI内核成功: {model_config.get('model_name')}")
            return kernel
            
        except Exception as e:
            logging.error(f"创建AI内核失败: {e}")
            raise
    
    async def _configure_ai_service_with_model(self, kernel: Kernel, model_provider: str, model_name: str, base_url: str, api_key: str):
        """使用模型配置配置AI服务"""
        try:
            if model_provider.lower() in ["openai", "deepseek", "silicon", "siliconflow", "qwen", "anthropic"]:
                # 配置OpenAI服务
                chat_service = OpenAIChatCompletion(
                    service_id="openai",
                    ai_model_id=model_name,
                    api_key=api_key,
                    endpoint=base_url
                )
                kernel.add_service(chat_service)
            elif model_provider.lower() == "azure":
                # 配置Azure OpenAI服务
                chat_service = AzureOpenAIChatCompletion(
                    service_id="azure_openai",
                    ai_model_id=model_name,
                    api_key=api_key,
                    endpoint=base_url
                )
                kernel.add_service(chat_service) 
            else:
                raise Exception(f"不支持的模型提供商: {model_provider}")
                
        except Exception as e:
            logging.error(f"配置AI服务失败: {e}")
            raise