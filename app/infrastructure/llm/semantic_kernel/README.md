# SemanticKernelService 使用指南

## 概述

`SemanticKernelService` 是一个基于 Microsoft Semantic Kernel 的AI服务封装类，提供了统一的接口来管理AI模型、插件和函数调用。

## 主要功能

- 🤖 **多模型支持**: 支持 OpenAI、Azure OpenAI、Anthropic 等主流AI服务
- 🔌 **插件管理**: 支持 Semantic Functions 和 Native Functions
- 💬 **对话管理**: 支持多轮对话和流式输出
- ⚙️ **灵活配置**: 支持自定义参数和配置

## 快速开始

### 1. 基础对话

```python
import asyncio
from app.infrastructure.llm.semantic_kernel.sk_service import SemanticKernelService

async def basic_chat():
    # 创建服务实例
    sk_service = SemanticKernelService(provider="openai", model="gpt-4o")
    
    # 准备消息
    messages = [
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ]
    
    # 发送消息
    response = await sk_service.invoke_prompt(
        messages=messages,
        system_prompt="你是一个友好的AI助手"
    )
    
    print(f"AI回复: {response}")

# 运行
asyncio.run(basic_chat())
```

### 2. 流式输出

```python
async def stream_chat():
    sk_service = SemanticKernelService()
    
    messages = [
        {"role": "user", "content": "请写一首诗"}
    ]
    
    print("AI回复: ", end="")
    async for chunk in sk_service.invoke_prompt_stream(
        messages=messages,
        system_prompt="你是一个诗人"
    ):
        print(chunk, end="", flush=True)
    print()

asyncio.run(stream_chat())
```

### 3. 多轮对话

```python
async def multi_turn_chat():
    sk_service = SemanticKernelService()
    
    # 模拟多轮对话
    conversation = [
        {"role": "user", "content": "我想学习Python"},
        {"role": "assistant", "content": "很好！你想从哪个方面开始？"},
        {"role": "user", "content": "基础语法"}
    ]
    
    response = await sk_service.invoke_prompt(
        messages=conversation,
        system_prompt="你是一个Python编程导师"
    )
    
    print(f"导师回复: {response}")

asyncio.run(multi_turn_chat())
```

## 插件使用

### 1. Semantic Functions

创建插件目录结构：
```
plugins/
├── code_analysis/
│   ├── config.json
│   └── skprompt.txt
└── file_operations/
    ├── config.json
    └── skprompt.txt
```

加载插件：
```python
async def load_plugins():
    sk_service = SemanticKernelService()
    
    # 加载插件
    success = await sk_service.add_semantic_functions("plugins")
    if success:
        print("插件加载成功")
    
    # 调用插件函数
    result = await sk_service.invoke_plugin_function(
        plugin_name="code_analysis",
        function_name="analyze_code",
        code="def hello(): print('Hello World')",
        analysis_type="complexity"
    )
    print(f"分析结果: {result}")

asyncio.run(load_plugins())
```

### 2. Native Functions

```python
from semantic_kernel.plugin_definition import kernel_function

class MathFunctions:
    @kernel_function(description="计算两个数的和", name="add")
    def add_numbers(self, a: float, b: float) -> float:
        return a + b

async def use_native_functions():
    sk_service = SemanticKernelService()
    
    # 添加Native Function
    math_func = MathFunctions()
    await sk_service.add_native_functions(math_func, "math_operations")
    
    # 使用函数
    messages = [
        {"role": "user", "content": "请计算 15 + 25"}
    ]
    
    response = await sk_service.invoke_prompt(
        messages=messages,
        system_prompt="你是一个数学助手，可以使用数学函数",
        auto_calls=True
    )
    print(f"计算结果: {response}")

asyncio.run(use_native_functions())
```

## 配置说明

### 1. 模型配置

在 `app/config/chat_models.json` 中配置模型：

```json
{
  "default": {
    "provider": "openai",
    "model": "gpt-4o"
  },
  "models": {
    "openai": {
      "is_valid": 1,
      "api_key": "your-api-key",
      "base_url": "https://api.openai.com/v1",
      "instances": {
        "gpt-4o": {
          "max_tokens": 4000,
          "temperature": 0.7
        }
      }
    }
  }
}
```

### 2. 服务创建参数

```python
sk_service = SemanticKernelService(
    provider="openai",           # 服务提供商
    model="gpt-4o",             # 模型名称
    api_key="your-api-key",     # API密钥（可选）
    temperature=0.7,            # 温度参数
    max_tokens=2000            # 最大token数
)
```

## API 参考

### 主要方法

#### `invoke_prompt(messages, system_prompt=None, auto_calls=True, **kwargs)`
- **功能**: 执行非流式Prompt调用
- **参数**:
  - `messages`: 对话消息列表
  - `system_prompt`: 系统提示词
  - `auto_calls`: 是否自动调用工具
  - `**kwargs`: 其他参数（temperature, max_tokens等）
- **返回**: 完整响应字符串

#### `invoke_prompt_stream(messages, system_prompt=None, auto_calls=True, **kwargs)`
- **功能**: 执行流式Prompt调用
- **参数**: 同 `invoke_prompt`
- **返回**: 异步生成器，产生流式响应块

#### `invoke_plugin_function(plugin_name, function_name, **kwargs)`
- **功能**: 调用插件函数
- **参数**:
  - `plugin_name`: 插件名称
  - `function_name`: 函数名称
  - `**kwargs`: 函数参数
- **返回**: 执行结果字符串

#### `invoke_plugin_function_stream(plugin_name, function_name, **kwargs)`
- **功能**: 流式调用插件函数
- **参数**: 同 `invoke_plugin_function`
- **返回**: 异步生成器，产生流式响应块

#### `add_semantic_functions(path)`
- **功能**: 添加Semantic Functions插件
- **参数**: `path` - 插件目录路径
- **返回**: 是否成功加载

#### `add_native_functions(function_instance, function_name=None)`
- **功能**: 添加Native Functions
- **参数**:
  - `function_instance`: 函数实例
  - `function_name`: 函数名称（可选）
- **返回**: 是否成功添加

## 错误处理

```python
try:
    sk_service = SemanticKernelService(provider="openai", model="gpt-4o")
    response = await sk_service.invoke_prompt(messages=messages)
    print(response)
except ValueError as e:
    print(f"配置错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

## 最佳实践

1. **错误处理**: 始终使用 try-catch 处理可能的异常
2. **资源管理**: 合理使用流式输出，避免内存占用过大
3. **参数调优**: 根据具体场景调整 temperature 和 max_tokens
4. **插件设计**: 插件函数应该有清晰的描述和参数定义
5. **日志记录**: 利用内置的日志系统进行调试和监控

## 示例文件

- `example_usage.py`: 完整的使用示例
- `quick_start.py`: 快速开始示例
- `plugin_example/`: 插件配置示例

## 依赖要求

- Python 3.8+
- semantic-kernel >= 1.35.2
- 其他依赖见 `requirements.txt`

## 许可证

本项目遵循项目主许可证。
