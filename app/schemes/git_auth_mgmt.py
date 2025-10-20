from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class GitAuthProvider(Enum):
    """Git认证提供商"""
    GITHUB = "github"
    GITEE = "gitee"
    GITLAB = "gitlab"

class GitAuthResponse(BaseModel):
    """Git认证信息响应"""
    id: str
    user_id: str
    provider: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GitAuthListResponse(BaseModel):
    """Git认证信息列表响应"""
    items: list[GitAuthResponse]
    total: int