import os
import re
import glob
from typing import List, Optional
from .BaseParser import BaseParser, Function


class PythonParser(BaseParser):
    def extract_imports(self, file_content: str) -> List[str]:
        """
        提取Python文件中的所有导入语句
        
        作用：从Python源代码中提取所有的import和from...import语句，返回导入的模块路径列表
        
        入参：
            file_content (str): Python文件的完整内容
        
        出参：
            List[str]: 导入的模块路径列表，例如 ["os", "sys", "utils.helper", ".", "..parent"]
        
        示例：
            import os
            import sys
            from utils import helper
            from . import local_module
            from ..parent import child
            from ...grandparent.module import func
            # 返回: ["os", "sys", "utils", ".", "..parent", "...grandparent.module"]
        """
        imports: List[str] = []

        # 匹配import语句
        import_regex = re.compile(r"import\s+([^\s,;]+)(?:\s*,\s*([^\s,;]+))*")
        for m in import_regex.finditer(file_content):
            for i in range(1, len(m.groups()) + 1):
                if m.group(i) and m.group(i).strip():
                    imports.append(m.group(i))
        
        # 匹配from...import语句
        from_import_regex = re.compile(r"from\s+([^\s]+)\s+import\s+(?:([^\s,;]+)(?:\s*,\s*([^\s,;]+))*|\*)")
        for m in from_import_regex.finditer(file_content):
            imports.append(m.group(1))
        return imports

    def extract_functions(self, file_content: str) -> List[Function]:
        """
        提取Python文件中的所有函数定义
        
        作用：从Python源代码中提取所有的函数定义，包括函数名和函数体
        
        入参：
            file_content (str): Python文件的完整内容
        
        出参：
            List[Function]: 函数对象列表，每个Function包含name和body属性
        
        示例：
            def hello_world():
                print("Hello, World!")
            
            def add(a: int, b: int) -> int:
                return a + b
            # 返回: [Function(name="hello_world", body="..."), Function(name="add", body="...")]
        """
        functions: List[Function] = []

        # 匹配函数声明
        func_regex = re.compile(r"def\s+(\w+)\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:(.*?)(?=\n(?:def|class)|\Z)", re.DOTALL)
        for m in func_regex.finditer(file_content):
            functions.append(Function(name=m.group(1), body=m.group(2) or ""))
        return functions

    def extract_function_calls(self, function_body: str) -> List[str]:
        """
        提取函数体中的所有函数调用
        
        作用：从函数体中提取所有的函数调用和方法调用，过滤掉Python内置函数和关键字
        
        入参：
            function_body (str): 函数的完整代码体
        
        出参：
            List[str]: 函数调用名称列表，过滤掉内置函数
        
        示例：
            def example():
                print("hello")           # 被过滤掉（内置函数）
                result = my_func()       # 匹配到：my_func
                data.append(item)        # 匹配到：append
                length = len(data)       # 被过滤掉（内置函数）
            # 返回: ["my_func", "append"]
        """
        calls: List[str] = []

        # 匹配函数调用
        call_regex = re.compile(r"(\w+)\s*\(")
        for m in call_regex.finditer(function_body):
            name = m.group(1)
            if name not in {"print", "len", "int", "str", "list", "dict", "set", "tuple", "if", "while", "for"}:
                calls.append(name)

        # 匹配方法调用
        method_call_regex = re.compile(r"(\w+)\.(\w+)\s*\(")
        for m in method_call_regex.finditer(function_body):
            calls.append(m.group(2))
        return calls

    def resolve_import_path(self, imp: str, current_file_path: str, base_path: str) -> Optional[str]:
        """
        解析Python导入路径为实际的文件系统路径
        
        作用：将Python的import语句中的模块路径转换为实际的文件系统路径，支持相对导入和绝对导入
        
        入参：
            imp (str): 导入的模块路径，例如 "os", "utils.helper", ".", "..parent"
            current_file_path (str): 当前文件的完整路径
            base_path (str): 项目根目录路径
        
        出参：
            Optional[str]: 解析后的实际文件路径，如果找不到则返回None
        
        示例：
            # 相对导入
            resolve_import_path(".", "/project/src/main.py", "/project") 
            # 返回: "/project/src/__init__.py"
            
            # 绝对导入
            resolve_import_path("utils", "/project/src/main.py", "/project")
            # 返回: "/project/utils.py" 或 "/project/utils/__init__.py"
            
            # 上级目录导入
            resolve_import_path("..parent", "/project/src/main.py", "/project")
            # 返回: "/project/parent.py" 或 "/project/parent/__init__.py"
        """
        current_dir = os.path.dirname(current_file_path)

        # 处理相对导入（以.开头）
        if imp.startswith('.'):
            parts = imp.split('.')
            dir_path = current_dir
            
            # 处理上级目录导入
            for i, part in enumerate(parts):
                if not part:  # 空字符串表示上级目录
                    dir_path = os.path.dirname(dir_path)
                else:
                    module_path = os.path.join(dir_path, part + '.py')
                    if os.path.isfile(module_path):
                        return module_path
                    
                    # 检查是否为包（目录）
                    package_path = os.path.join(dir_path, part)
                    init_path = os.path.join(package_path, '__init__.py')
                    if os.path.isdir(package_path) and os.path.isfile(init_path):
                        return init_path
        # 处理绝对导入
        else:
            # 搜索整个项目中的模块
            module_name = imp.split('.')[0]
            possible_files = glob.glob(os.path.join(base_path, "**", module_name + ".py"), recursive=True)
            
            if possible_files:
                return possible_files[0]
            
            # 搜索包
            possible_dirs = glob.glob(os.path.join(base_path, "**", module_name), recursive=True)
            for dir_path in possible_dirs:
                if os.path.isdir(dir_path):
                    init_path = os.path.join(dir_path, '__init__.py')
                    if os.path.isfile(init_path):
                        return init_path
        
        return None

    def get_function_line_number(self, file_content: str, function_name: str) -> int:
        """
        获取指定函数在文件中的行号
        
        作用：在Python文件中查找指定函数名的函数定义，返回其所在的行号
        
        入参：
            file_content (str): Python文件的完整内容
            function_name (str): 要查找的函数名
        
        出参：
            int: 函数定义所在的行号，如果找不到则返回0
        
        示例：
            def hello_world():     # 第1行
                pass
            
            def add(a, b):         # 第4行
                return a + b
            
            get_function_line_number(content, "add")  # 返回: 4
            get_function_line_number(content, "not_found")  # 返回: 0
        """
        lines = file_content.split('\n')
        
        func_regex = re.compile(rf"def\s+{re.escape(function_name)}\s*\(")
        for i, line in enumerate(lines, 1):
            if func_regex.search(line):
                return i
        return 0 