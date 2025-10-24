"""
语义分析器模块

提供各种编程语言的语义分析功能，包括：
- 基础语义分析器接口
- Go语言语义分析器
- 项目语义模型
"""

from .base import (
    BaseSemanticAnalyzer,
    ProjectSemanticModel,
    SemanticModel,
    TypeInfo,
    FunctionInfo,
    VariableInfo,
    ImportInfo,
    ParameterInfo,
    FunctionCallInfo,
    TypeKind,
    AccessModifier
)

from .go_semantic_analyzer import GoSemanticAnalyzer

__all__ = [
    'BaseSemanticAnalyzer',
    'ProjectSemanticModel', 
    'SemanticModel',
    'TypeInfo',
    'FunctionInfo',
    'VariableInfo',
    'ImportInfo',
    'ParameterInfo',
    'FunctionCallInfo',
    'TypeKind',
    'AccessModifier',
    'GoSemanticAnalyzer'
]
