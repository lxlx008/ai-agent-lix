from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agents.personal_agent import search_recipes, get_message, clear_messages
from app.models.schemas import ChatRequest

router = APIRouter()


@router.post("/chat/stream")
async def chat_endpoint(request: ChatRequest):
    """流式对话"""
    return StreamingResponse(search_recipes(request.message, request.image_url, request.thread_id),
                             media_type="text/event-stream")


@router.get("/chat/messages")
async def get_chat_messages(thread_id: str):
    """获取历史消息"""
    return {"messages": get_message(thread_id)}


@router.delete("/chat/messages")
async def clear_chat_messages(thread_id: str):
    """清空历史消息"""
    clear_messages(thread_id)
    return {"success": True}
