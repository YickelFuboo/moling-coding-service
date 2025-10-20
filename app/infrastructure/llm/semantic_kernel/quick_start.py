"""
SemanticKernelService 快速开始示例

最简单的使用方式
"""

import asyncio
from app.infrastructure.llm.semantic_kernel.sk_service import SemanticKernelService


async def quick_start():
    """快速开始示例"""
    
    # 1. 创建服务实例（使用默认配置）
    sk_service = SemanticKernelService()
    
    # 2. 准备对话消息
    messages = [
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ]
    
    # 3. 发送消息并获取回复
    response = await sk_service.invoke_prompt(
        messages=messages,
        system_prompt="你是一个友好的AI助手"
    )
    
    print(f"AI回复: {response}")


async def stream_example():
    """流式输出示例"""
    
    sk_service = SemanticKernelService()
    
    messages = [
        {"role": "user", "content": "请写一首短诗"}
    ]
    
    print("AI回复: ", end="")
    async for chunk in sk_service.invoke_prompt_stream(
        messages=messages,
        system_prompt="你是一个诗人"
    ):
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    # 运行快速开始示例
    asyncio.run(quick_start())
    
    # 运行流式示例
    asyncio.run(stream_example())
