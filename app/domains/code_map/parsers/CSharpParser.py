import os
import re
from typing import List, Optional
from .BaseParser import BaseParser, Function


class CSharpParser(BaseParser):
    def extract_imports(self, file_content: str) -> List[str]:
        imports: List[str] = []
        
        # 匹配 using 语句
        using_regex = re.compile(r"using\s+([^;]+);")
        for m in using_regex.finditer(file_content):
            import_name = m.group(1).strip()
            # 过滤掉 using static 和 using alias
            if not import_name.startswith("static ") and "=" not in import_name:
                imports.append(import_name)
        
        return imports

    def extract_functions(self, file_content: str) -> List[Function]:
        functions: List[Function] = []
        
        # 匹配方法声明（包括各种访问修饰符和返回类型）
        method_regex = re.compile(
            r"(?:public|private|protected|internal|static|virtual|override|abstract|async)?\s*"
            r"(?:public|private|protected|internal|static|virtual|override|abstract|async)?\s*"
            r"(?:public|private|protected|internal|static|virtual|override|abstract|async)?\s*"
            r"(?:public|private|protected|internal|static|virtual|override|abstract|async)?\s*"
            r"(?:public|private|protected|internal|static|virtual|override|abstract|async)?\s*"
            r"(?:public|private|protected|internal|static|virtual|override|abstract|async)?\s*"
            r"(?:public|private|protected|internal|static|virtual|override|abstract|async)?\s*"
            r"(?:public|private|protected|internal|static|virtual|override|abstract|async)?\s*"
            r"(?:public|private|protected|internal|static|virtual|override|abstract|async)?\s*"
            r"(?:public|private|protected|internal|static|virtual|override|abstract|async)?\s*"
            r"(?:public|private|protected|internal|static|virtual|override|abstract|async)?\s*"
            r"(?:public|private|protected|internal|static|virtual|override|abstract|async)?\s*"
            r"(?:[a-zA-Z0-9_<>,\s\[\]]+\s+)?([a-zA-Z0-9_]+)\s*\([^)]*\)\s*"
            r"(?:where\s+[^{]+)?\s*\{([^{}]*(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}[^{}]*)*)\}"
        )
        
        for m in method_regex.finditer(file_content):
            name = m.group(1)
            body = m.group(2) or ""
            
            # 过滤掉构造函数、析构函数和关键字
            if not name.startswith("~") and name not in {"if", "for", "while", "switch", "catch", "get", "set"}:
                functions.append(Function(name=name, body=body))
        
        return functions

    def extract_function_calls(self, function_body: str) -> List[str]:
        calls: List[str] = []
        
        try:
            # 尝试解析方法调用，模拟C#的语法树解析
            # 匹配方法调用：object.Method() 或 Method()
            call_regex = re.compile(r"(?:[a-zA-Z0-9_]+\.)?([a-zA-Z0-9_]+)\s*\(")
            
            for m in call_regex.finditer(function_body):
                name = m.group(1)
                # 过滤一些常见的关键字
                if name not in {"if", "for", "while", "switch", "catch", "new", "typeof", "sizeof"}:
                    calls.append(name)
                    
        except Exception:
            # 使用正则表达式作为备用解析方法（与C#版本一致）
            call_regex = re.compile(r"(\w+)\s*\(")
            for m in call_regex.finditer(function_body):
                name = m.group(1)
                if name not in {"if", "for", "while", "switch", "catch"}:
                    calls.append(name)
        
        return calls

    def resolve_import_path(self, import_name: str, current_file_path: str, base_path: str) -> Optional[str]:
        # C#使用命名空间而非直接引用文件，需要解析项目文件
        current_dir = os.path.dirname(current_file_path)
        
        # 尝试从项目中查找类型
        parts = import_name.split('.')
        type_name = parts[-1] if parts else import_name
        
        # 在项目中查找包含此类型名称的文件
        import os
        import glob
        possible_files = glob.glob(os.path.join(base_path, "**", "*.cs"), recursive=True)
        
        for file_path in possible_files:
            if file_path == current_file_path:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查文件是否包含此类型声明
                if (f"class {type_name}" in content or 
                    f"struct {type_name}" in content or 
                    f"interface {type_name}" in content or 
                    f"enum {type_name}" in content):
                    
                    # 检查命名空间是否匹配
                    if len(parts) > 1:
                        namespace_parts = '.'.join(parts[:-1])
                        namespace_regex = re.compile(rf"namespace\s+{re.escape(namespace_parts)}\s*\{{")
                        if namespace_regex.search(content):
                            return file_path
                    else:
                        # 如果没有命名空间，直接返回
                        return file_path
                        
            except Exception:
                continue
        
        return None

    def get_function_line_number(self, file_content: str, function_name: str) -> int:
        lines = file_content.split('\n')
        method_regex = re.compile(rf"\b{re.escape(function_name)}\s*\(")
        
        for i, line in enumerate(lines):
            if method_regex.search(line) and any(keyword in line for keyword in 
                ["void", "int", "string", "bool", "object", "Task"]):
                return i + 1
        
        return 0
