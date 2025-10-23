from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship


class DocumentCommitRecord:
    """文档提交记录模型"""
    __tablename__ = "document_commit_records"
    
    id = Column(String(36), primary_key=True, index=True, comment="ID")
    repo_id = Column(String(36), ForeignKey("repo_records.id"), nullable=False, comment="仓库ID")
    
    commit_id = Column(String(100), nullable=False, default="", comment="提交ID")
    commit_message = Column(String(1000), nullable=False, default="", comment="提交消息")
    title = Column(String(200), nullable=False, default="", comment="标题")
    author = Column(String(100), nullable=False, default="", comment="作�?)
    
    # 时间�?
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # 关联关系
    repo_record = relationship("RepoRecord", back_populates="commit_records")
    
    def to_dict(self):
        """转换为字�?""
        return {
            "id": self.id,
            "repo_id": self.repo_id,
            "commit_id": self.commit_id,
            "commit_message": self.commit_message,
            "title": self.title,
            "author": self.author,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 
