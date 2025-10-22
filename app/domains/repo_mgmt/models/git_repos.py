from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship


class RepoRecordStatus:
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


class RepoRecord():
    """仓库模型"""
    __tablename__ = "repo_records"
    
    id = Column(String, primary_key=True, index=True, comment="ID")
    create_user_id = Column(String, nullable=False, comment="创建用户ID")
    
    # git相关字段    
    git_type = Column(String, default="git", comment="仓库类型")
    repo_url = Column(String, default="", comment="仓库URL")
    repo_organization = Column(String, nullable=False, default="", comment="组织")
    repo_name = Column(String, nullable=False, comment="仓库名称")
    repo_description = Column(Text, default="", comment="仓库介绍")    
    repo_branch = Column(String, default="main", comment="分支")    
    
    # git本地行相关信息
    local_path = Column(String, nullable=True, comment="本地路径")
    version = Column(String, nullable=True, comment="版本")
    
    # 优化信息
    optimized_directory_struct = Column(Text, nullable=True, comment="优化目录结构")
    readme_content = Column(Text, nullable=True, comment="README内容")
    repo_classify = Column(String, nullable=True, comment="分类")  
    prompt = Column(Text, nullable=True, comment="提示词")
    
    # 嵌入完成标志
    is_embedded = Column(Boolean, default=False, comment="是否嵌入完成")
    # 是否推荐
    is_recommended = Column(Boolean, default=False, comment="是否推荐")
    # 是否公开
    is_public = Column(Boolean, default=False, comment="是否公开")

    # 仓库信息
    status = Column(String, default=RepoRecordStatus.Pending, comment="仓库状态")
    error = Column(Text, nullable=True, comment="错误信息")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    def to_dict(self):
        """转换为字典"""
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
            "status": self.status,
            "error": self.error,
            "prompt": self.prompt,
            "is_embedded": self.is_embedded,
            "is_recommended": self.is_recommended,
            "is_public": self.is_public,
            "optimized_directory_structure": self.optimized_directory_struct,
            "readme": self.readme_content,
            "classify": self.repo_classify
        } 