"""
Conversation management endpoints for the Enterprise AI System.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.middleware.auth import get_current_user

router = APIRouter()

@router.get("/")
async def list_conversations(current_user = Depends(get_current_user)):
    """List conversations."""
    raise HTTPException(status_code=501, detail="Not implemented")

@router.post("/")
async def create_conversation(current_user = Depends(get_current_user)):
    """Create conversation."""
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str, current_user = Depends(get_current_user)):
    """Get conversation by ID."""
    raise HTTPException(status_code=501, detail="Not implemented")

