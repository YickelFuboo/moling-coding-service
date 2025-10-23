from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship


class RepoRecord:
    """仓库模型"""
    __tablename__ = "repo_records"
    
    id = Column(String, primary_key=True, index=True, comment="ID")
    create_user_id = Column(String, nullable=False, comment="创建用户ID")
    
    # 仓库基本信息
    git_type = Column(String, default="git", comment="仓库类型")
    repo_url = Column(String, default="", comment="仓库URL")
    repo_organization = Column(String, nullable=False, default="", comment="组织")
    repo_name = Column(String, nullable=False, comment="仓库名称")
    repo_description = Column(Text, default="", comment="仓库介绍")    
    repo_branch = Column(String, default="main", comment="分支")    
    
    # 本地路径信息
    local_path = Column(String, nullable=True, comment="本地路径")
    version = Column(String, nullable=True, comment="版本")
    
    # 各种装填标志完成标志
    is_embedded = Column(Boolean, default=False, comment="是否嵌入完成")
    is_chunked = Column(Boolean, default=False, comment="是否嵌入完成")

    # 时间�?
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # 关联关系
    commit_records = relationship("DocumentCommitRecord", back_populates="repo_record", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "create_user_id": self.create_user_id,
            "git_type": self.git_type,
            "repo_url": self.repo_url,
            "repo_organization": self.repo_organization,
            "repo_name": self.repo_name,
            "repo_description": self.repo_description,
            "repo_branch": self.repo_branch,
            "local_path": self.local_path,
            "version": self.version,
            "is_embedded": self.is_embedded,
            "is_chunked": self.is_chunked,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 
