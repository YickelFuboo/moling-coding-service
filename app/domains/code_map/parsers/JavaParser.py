import os
import re
import glob
from typing import List, Optional
from .BaseParser import BaseParser, Function


class JavaParser(BaseParser):
    # 提取导入语句
    def extract_imports(self, file_content: str) -> List[str]:
        imports: List[str] = []

        import_regex = re.compile(r"import\s+([^;]+);")
        for m in import_regex.finditer(file_content):
            imports.append(m.group(1).strip())
        return imports

    # 提取函数
    def extract_functions(self, file_content: str) -> List[Function]:
        functions: List[Function] = []

        method_regex = re.compile(
            r'(?:public|private|protected|static|\s) +(?:[a-zA-Z0-9_\.<>\[\]]+) +([a-zA-Z0-9_]+) *\([@a-zA-Z0-9_<>\[\]\(\)"=,\s.]*\) *(?:throws [^{]*)?\{([^{}]*(?:\{[^{}]*(?:\{[^{}]*(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}[^{}]*)*\}[^{}]*)*\}[^{}]*)*)\}',
            re.DOTALL,
        )
        for m in method_regex.finditer(file_content):
            name = m.group(1)
            if name not in {"if", "for", "while", "switch", "catch"}:
                functions.append(Function(name=name, body=m.group(2) or ""))
        return functions

    # 提取函数调用
    def extract_function_calls(self, function_body: str) -> List[str]:
        calls: List[str] = []
        
        call_regex = re.compile(r"(?:\b[a-zA-Z0-9_]+\.)?\b([a-zA-Z0-9_]+)\s*\(")
        for m in call_regex.finditer(function_body):
            name = m.group(1)
            if name not in {"if", "for", "while", "switch", "catch"}:
                calls.append(name)
        return calls

    # 解析导入路径
    def resolve_import_path(self, imp: str, current_file_path: str, base_path: str) -> Optional[str]:
        parts = imp.split('.')
        class_name = parts[-1]
        
        # 处理wildcard导入
        if class_name == "*":
            class_name = ""
        
        # 在项目中搜索类文件
        possible_files = glob.glob(os.path.join(base_path, "**", "*.java"), recursive=True)
        
        for file_path in possible_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                
                if not class_name:
                    # 检查包声明是否匹配
                    package_regex = re.compile(rf"package\s+{re.escape('.'.join(parts[:-1]))};")
                    if package_regex.search(content):
                        return file_path
                elif os.path.splitext(os.path.basename(file_path))[0].lower() == class_name.lower():
                    # 检查包声明是否匹配
                    package_regex = re.compile(rf"package\s+{re.escape('.'.join(parts[:-1]))};")
                    if package_regex.search(content):
                        return file_path
            except Exception:
                continue
        return None

    # 获取函数行号
    def get_function_line_number(self, file_content: str, function_name: str) -> int:
        lines = file_content.split('\n')
        
        method_regex = re.compile(rf"(?:public|private|protected|static|\s) +(?:[a-zA-Z0-9_\.<>\[\]]+) +{re.escape(function_name)} *\(")
        for i, line in enumerate(lines, 1):
            if method_regex.search(line):
                return i
        return 0 