from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship


class DocumentOverview:
    """文档概述模型"""
    __tablename__ = "document_overviews"
    
    id = Column(String(36), primary_key=True, index=True, comment="ID")
    wiki_document_id = Column(String(36), ForeignKey("wiki_documents.id"), nullable=False, comment="文档ID")
    content = Column(Text, nullable=False, default="", comment="内容")
    title = Column(String(200), nullable=False, default="", comment="标题")
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # 关联关系
    wiki_document = relationship("WikiDocument", back_populates="overview")
    
    def to_dict(self):
        return {
            "id": self.id,
            "wiki_document_id": self.wiki_document_id,
            "content": self.content,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 
