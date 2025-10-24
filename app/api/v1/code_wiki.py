from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.domains.repo_mgmt.services.repo_mgmt_service import RepoMgmtService
from app.domains.code_wiki.services.wiki_document_service import WikiDocumentService

router = APIRouter(tags=["代码Wiki管理"])


@router.post("/{repository_id}/generate")
async def generate_repository_wiki(
    repository_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db)
):
    """启动仓库wiki生成任务"""
    try:
        # 检查仓库是否存在
        repository = await RepoMgmtService.get_repository_by_id(db, repository_id)
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        if repository.create_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限操作该仓库"
            )
        
        # 检查仓库是否已克隆
        if not repository.is_cloned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="仓库尚未克隆完成，请等待克隆完成后再生成wiki"
            )
        
        # 启动wiki生成任务
        wiki_document = await WikiDocumentService.create_wiki_document(
            session=db,
            repo_id=repository_id
        )
        
        return {
            "message": "Wiki生成任务已启动", 
            "repository_id": repository_id,
            "document_id": wiki_document.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动wiki生成任务失败: {str(e)}"
        )

