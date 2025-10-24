from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship


class WikiGenStatus:
    """仓库状态枚举"""
    Pending = "pending"
    Processing = "processing"
    Completed = "completed"
    Canceled = "canceled"
    Unauthorized = "unauthorized"
    Failed = "failed"

class RepoClassify:
    """项目分类枚举"""
    Applications = "Applications"
    Frameworks = "Frameworks"
    Libraries = "Libraries"
    DevelopmentTools = "DevelopmentTools"
    CLITools = "CLITools"
    DevOpsConfiguration = "DevOpsConfiguration"
    Documentation = "Documentation"

class WikiDocument:
    """支持嵌架构文模型"""
    __tablename__ = "wiki_documents"
    
    id = Column(String, primary_key=True, index=True, comment="ID")
    
    # 代码仓信息 - 与RepoRecord建立外键关系
    repo_id = Column(String, ForeignKey("repo_records.id"), nullable=False, index=True, comment="代码仓对象库ID")    
    path = Column(String, default="", nullable=False, comment="本地地址")
    
    # 嵌套关系
    parent_id = Column(String, ForeignKey("wiki_documents.id"), nullable=True, comment="父文档ID")
    
    # 代码仓wiki解析相关信息
    is_boot = Column(Boolean, default=False, comment="是否嵌入完成")   
    # 代码仓分类，信息，boot Document需要记录
    repo_classify = Column(String, nullable=True, comment="分类") 

    # 文档基本信息
    description = Column(Text, default="", comment="文档介绍")
    
    # 优化信息    
    optimized_directory_struct = Column(Text, nullable=True, comment="优化目录结构")
    readme_content = Column(Text, nullable=True, comment="README内容")

    # 状态信息
    status = Column(String, default=WikiGenStatus.Pending, nullable=False, comment="文档状态")
    error = Column(Text, nullable=True, comment="错误信息")

    # 统计信息
    last_update = Column(DateTime, default=datetime.utcnow, nullable=False, comment="最后更新时间")
    like_count = Column(Integer, default=0, nullable=False, comment="浏览量")
    comment_count = Column(Integer, default=0, nullable=False, comment="评论量")
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # 与RepoRecord的关系
    repo_record = relationship("RepoRecord", back_populates="wiki_documents")
    
    # 嵌套关系
    parent = relationship("WikiDocument", remote_side=[id], back_populates="children")
    children = relationship("WikiDocument", back_populates="parent", cascade="all, delete-orphan")
    
    # 文档概述关系
    overview = relationship("DocumentOverview", back_populates="wiki_document", uselist=False, cascade="all, delete-orphan")
    
    def to_dict(self, include_children=False):
        result = {
            "id": self.id,
            "repo_id": self.repo_id,
            "path": self.path,
            "parent_id": self.parent_id,
            "is_boot": self.is_boot,
            "repo_classify": self.repo_classify,
            "description": self.description,
            "optimized_directory_struct": self.optimized_directory_struct,
            "readme_content": self.readme_content,
            "status": self.status,
            "error": self.error,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "name": self.get_name(),
        }
        
        if include_children and self.children:
            result["children"] = [child.to_dict(include_children=True) for child in self.children]
        
        return result
    
    def get_name(self):
        """从path获取名称"""
        if self.path:
            return self.path.split('/')[-1] if '/' in self.path else self.path
        return ""
    
    def get_full_path(self):
        """获取完整路径"""
        return self.path
    
    def get_ancestors(self):
        """获取所有祖先节点"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors
    
    def get_descendants(self):
        """获取所有后代节点"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def is_root(self):
        """是否为根节点"""
        return self.parent_id is None
    
    def is_leaf(self):
        """是否为叶子节点"""
        return len(self.children) == 0
    
    def __repr__(self):
        return f"<WikiDocument(id='{self.id}', name='{self.get_name()}')>" 
