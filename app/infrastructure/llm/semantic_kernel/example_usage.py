"""
SemanticKernelService 使用示例

本示例展示了如何使用SemanticKernelService进行AI对话、插件管理和函数调用
"""

import asyncio
from typing import List, Dict
from app.infrastructure.llm.semantic_kernel.sk_service import SemanticKernelService
from app.utils.logger import logger


async def basic_chat_example():
    """基础对话示例"""
    print("=== 基础对话示例 ===")
    
    # 创建SemanticKernelService实例
    sk_service = SemanticKernelService()
    
    # 准备对话消息
    messages = [
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ]
    
    try:
        # 非流式调用
        response = await sk_service.invoke_prompt(
            messages=messages,
            system_prompt="你是一个友好的AI助手",
            auto_calls=True,
            temperature=0.7
        )
        print(f"AI回复: {response}")
        
    except Exception as e:
        logger.error(f"对话失败: {e}")


async def stream_chat_example():
    """流式对话示例"""
    print("\n=== 流式对话示例 ===")
    
    sk_service = SemanticKernelService()
    
    messages = [
        {"role": "user", "content": "请写一首关于春天的诗"}
    ]
    
    try:
        print("AI回复: ", end="")
        # 流式调用
        async for chunk in sk_service.invoke_prompt_stream(
            messages=messages,
            system_prompt="你是一个诗人",
            auto_calls=True,
            temperature=0.8
        ):
            print(chunk, end="", flush=True)
        print()  # 换行
        
    except Exception as e:
        logger.error(f"流式对话失败: {e}")


async def multi_turn_conversation_example():
    """多轮对话示例"""
    print("\n=== 多轮对话示例 ===")
    
    sk_service = SemanticKernelService()
    
    # 模拟多轮对话
    conversation = [
        {"role": "user", "content": "我想学习Python编程"},
        {"role": "assistant", "content": "很好！Python是一门优秀的编程语言。你想从哪个方面开始学习？"},
        {"role": "user", "content": "我想学习基础语法"}
    ]
    
    try:
        response = await sk_service.invoke_prompt(
            messages=conversation,
            system_prompt="你是一个Python编程导师，请耐心指导学生",
            auto_calls=True,
            temperature=0.6
        )
        print(f"导师回复: {response}")
        
    except Exception as e:
        logger.error(f"多轮对话失败: {e}")


async def plugin_management_example():
    """插件管理示例"""
    print("\n=== 插件管理示例 ===")
    
    sk_service = SemanticKernelService()
    
    try:
        # 添加Semantic Functions插件
        # 假设您有一个插件目录结构：
        # plugins/
        # ├── code_analysis/
        # │   ├── config.json
        # │   └── skprompt.txt
        # └── file_operations/
        #     ├── config.json
        #     └── skprompt.txt
        
        success = await sk_service.add_semantic_functions("plugins")
        if success:
            print("插件加载成功")
        else:
            print("插件加载失败")
            
    except Exception as e:
        logger.error(f"插件管理失败: {e}")


async def plugin_function_call_example():
    """插件函数调用示例"""
    print("\n=== 插件函数调用示例 ===")
    
    sk_service = SemanticKernelService(provider="openai", model="gpt-4o")
    
    try:
        # 调用插件函数
        result = await sk_service.invoke_plugin_function(
            plugin_name="code_analysis",
            function_name="analyze_file",
            file_path="/path/to/example.py",
            analysis_type="complexity"
        )
        print(f"代码分析结果: {result}")
        
    except Exception as e:
        logger.error(f"插件函数调用失败: {e}")


async def plugin_function_stream_example():
    """插件函数流式调用示例"""
    print("\n=== 插件函数流式调用示例 ===")
    
    sk_service = SemanticKernelService()
    
    try:
        print("代码分析结果: ", end="")
        # 流式调用插件函数
        async for chunk in sk_service.invoke_plugin_function_stream(
            plugin_name="code_analysis",
            function_name="generate_documentation",
            file_path="/path/to/example.py",
            format="markdown"
        ):
            print(chunk, end="", flush=True)
        print()  # 换行
        
    except Exception as e:
        logger.error(f"插件函数流式调用失败: {e}")


async def native_function_example():
    """Native Function示例"""
    print("\n=== Native Function示例 ===")
    
    from semantic_kernel.plugin_definition import kernel_function
    
    # 定义一个Native Function
    class MathFunctions:
        @kernel_function(
            description="计算两个数的和",
            name="add"
        )
        def add_numbers(self, a: float, b: float) -> float:
            """计算两个数的和"""
            return a + b
        
        @kernel_function(
            description="计算两个数的乘积",
            name="multiply"
        )
        def multiply_numbers(self, a: float, b: float) -> float:
            """计算两个数的乘积"""
            return a * b
    
    sk_service = SemanticKernelService()
    
    try:
        # 添加Native Function
        math_func = MathFunctions()
        success = await sk_service.add_native_functions(math_func, "math_operations")
        
        if success:
            print("Native Function添加成功")
            
            # 使用数学函数
            messages = [
                {"role": "user", "content": "请计算 15 + 25 的结果"}
            ]
            
            response = await sk_service.invoke_prompt(
                messages=messages,
                system_prompt="你是一个数学助手，可以使用数学函数进行计算",
                auto_calls=True
            )
            print(f"计算结果: {response}")
        else:
            print("Native Function添加失败")
            
    except Exception as e:
        logger.error(f"Native Function示例失败: {e}")


async def advanced_usage_example():
    """高级用法示例"""
    print("\n=== 高级用法示例 ===")
    
    # 使用自定义参数创建服务
    sk_service = SemanticKernelService(
        provider="openai",
        model="gpt-4o",
        api_key="your-api-key",  # 可选，会从配置文件读取
        temperature=0.8,
        max_tokens=2000
    )
    
    try:
        # 复杂的对话场景
        messages = [
            {"role": "user", "content": "请分析这段代码的性能问题"},
            {"role": "assistant", "content": "我需要看到具体的代码才能进行分析。"},
            {"role": "user", "content": "def slow_function(n):\n    result = []\n    for i in range(n):\n        result.append(i * 2)\n    return result"}
        ]
        
        response = await sk_service.invoke_prompt(
            messages=messages,
            system_prompt="你是一个代码性能分析专家，请提供详细的优化建议",
            auto_calls=True,
            temperature=0.5,
            max_tokens=1500
        )
        print(f"性能分析: {response}")
        
    except Exception as e:
        logger.error(f"高级用法示例失败: {e}")


async def error_handling_example():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    try:
        # 使用不存在的模型
        sk_service = SemanticKernelService(provider="invalid_provider", model="invalid_model")
        
    except ValueError as e:
        print(f"预期的错误: {e}")
    
    try:
        # 正常创建服务
        sk_service = SemanticKernelService(provider="openai", model="gpt-4o")
        
        # 调用不存在的插件函数
        await sk_service.invoke_plugin_function(
            plugin_name="non_existent_plugin",
            function_name="non_existent_function"
        )
        
    except ValueError as e:
        print(f"插件不存在错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")


async def main():
    """主函数 - 运行所有示例"""
    print("SemanticKernelService 使用示例")
    print("=" * 50)
    
    # 运行各种示例
    await basic_chat_example()
    await stream_chat_example()
    await multi_turn_conversation_example()
    await plugin_management_example()
    await plugin_function_call_example()
    await plugin_function_stream_example()
    await native_function_example()
    await advanced_usage_example()
    await error_handling_example()
    
    print("\n" + "=" * 50)
    print("所有示例运行完成！")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
