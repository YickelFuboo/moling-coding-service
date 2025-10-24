import os
import re
import glob
from typing import List, Optional
from .BaseParser import BaseParser, Function


class CppParser(BaseParser):
    def extract_imports(self, file_content: str) -> List[str]:
        imports: List[str] = []

        # 匹配 #include 语句
        include_regex = re.compile(r"#include\s+[<\"]([^>\"]+)[>\"]")
        for m in include_regex.finditer(file_content):
            imports.append(m.group(1))
        return imports

    def extract_functions(self, file_content: str) -> List[Function]:
        functions: List[Function] = []

        func_regex = re.compile(r"(?:(?:[a-zA-Z0-9_\*&\s:<>,]+)\s+)?([a-zA-Z0-9_]+)\s*\([^)]*\)\s*(?:const)?\s*(?:noexcept)?\s*(?:override)?\s*(?:final)?\s*(?:=\s*default)?\s*(?:=\s*delete)?\s*(?:=\s*0)?\s*\{([^{}]*(?:{[^{}]*(?:{[^{}]*}[^{}]*)*}[^{}]*)*)\}")
        for m in func_regex.finditer(file_content):
            name = m.group(1)
            if not name.startswith("~") and name not in {"if", "for", "while", "switch", "catch"}:
                functions.append(Function(name=name, body=m.group(2) or ""))
        return functions

    def extract_function_calls(self, function_body: str) -> List[str]:
        calls: List[str] = []

        call_regex = re.compile(r"(?:(?:[a-zA-Z0-9_]+)::)?([a-zA-Z0-9_]+)\s*\(")
        for m in call_regex.finditer(function_body):
            name = m.group(1)
            if name not in {"if", "for", "while", "switch", "catch"}:
                calls.append(name)
        return calls

    def resolve_import_path(self, imp: str, current_file_path: str, base_path: str) -> Optional[str]:
        current_dir = os.path.dirname(current_file_path)
        
        # 对于系统头文件，不尝试解析实际路径
        if "/" in imp or "\\" in imp:
            # 尝试在项目中查找头文件
            possible_files = glob.glob(os.path.join(base_path, "**", os.path.basename(imp)), recursive=True)
            if possible_files:
                return possible_files[0]
        else:
            # 查找当前目录和项目中的头文件
            local_path = os.path.join(current_dir, imp)
            if os.path.isfile(local_path):
                return local_path
            
            possible_files = glob.glob(os.path.join(base_path, "**", imp), recursive=True)
            if possible_files:
                return possible_files[0]
        
        return None

    def get_function_line_number(self, file_content: str, function_name: str) -> int:
        lines = file_content.split("\n")
        
        func_regex = re.compile(rf"(?:(?:[a-zA-Z0-9_\*&\s:<>,]+)\s+)?{re.escape(function_name)}\s*\(")
        for i, line in enumerate(lines, 1):
            if func_regex.search(line):
                return i
        return 0 