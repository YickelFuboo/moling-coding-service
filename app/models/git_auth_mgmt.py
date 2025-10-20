import uuid
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Index, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseEntity


class GitAuth(BaseEntity):
    """用户Git认证信息模型"""
    __tablename__ = "git_auths"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    provider = Column(String(20), nullable=False)
    token = Column(String(500), nullable=False)  # 访问令牌（加密存储）
    is_active = Column(Boolean, default=True)

    # 创建复合索引
    __table_args__ = (
        Index('idx_user_provider', 'user_id', 'provider'),
    )
    
    def __repr__(self):
        return f"<UserGitAuth(id={self.id}, user_id={self.user_id}, provider={self.provider})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "provider": self.provider,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        } 