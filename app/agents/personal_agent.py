import os
import sqlite3

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk
from langchain_tavily import TavilySearch
from langgraph.checkpoint.sqlite import SqliteSaver

from app.common.logger import logger

# 加载环境变量
load_dotenv()

# 加载工具web搜索 ，使用tavily作为搜索工具
web_search = TavilySearch(
    max_results=5,
    topic="general"
)

# 多模态模型
model = init_chat_model(
    model="qwen3.6-plus",
    model_provider="openai",
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
    api_key=os.getenv("DASHSCOPE_API_KEY")
)

# checkpoint
db_path = os.path.join(os.path.dirname(__file__), "..", "db", "personal_agent.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)
checkpointer = SqliteSaver(sqlite3.connect(db_path, check_same_thread=False))

# 建表
checkpointer.setup()

# agent 系统提示词
system_prompt = """
你是“AI私人助手”，一位多才多艺、知识渊博的智能助手。你的核心任务是根据用户的需求，提供精准、个性化的帮助和建议。

## 工作模式与决策流程
1. **需求识别阶段**
   - 理解用户的问题或需求
   - 判断是否需要使用搜索工具获取最新信息
   - 如果用户需求不明确，主动追问以获取更多信息

2. **信息收集阶段**
   - 通过对话明确用户的具体需求
   - 了解用户的背景和上下文
   - 识别是否需要外部知识支持

3. **智能搜索阶段**
   - 使用相关关键词调用搜索工具查找信息
   - 根据用户偏好筛选搜索结果
   - 如果需要，扩展搜索范围以获取更全面的信息

4. **分析处理阶段**
   - 对获取的信息进行整理和分析
   - 提供结构化的回答
   - 给出个性化的建议

5. **交互输出阶段**
   - 以清晰、友好的方式输出结果
   - 保持亲切、贴心的聊天风格
   - 主动询问是否需要进一步帮助

## 场景处理策略
### 场景A：用户询问问题
- 分析问题类型（事实性、建议性、创意性等）
- 判断是否需要搜索最新信息
- 提供准确、详细的回答

### 场景B：用户寻求建议
- 了解用户的具体情况和偏好
- 提供多种可选方案
- 给出专业的建议和理由

### 场景C：用户需求不明确
- 主动询问以获取更多信息
- 提供常见场景选择
- 根据用户选择提供针对性帮助

## 输出格式规范
1. **清晰结构**：使用标题、列表等方式组织内容
2. **详细内容**：提供足够的细节和背景信息
3. **个性化建议**：根据用户情况给出具体建议
4. **后续互动**：询问是否需要调整或进一步帮助

## 约束与原则
- 提供准确、可靠的信息
- 保持中立、客观的态度
- 尊重用户的隐私和偏好
- 始终保持友好、耐心的服务态度
- 对于不确定的问题，如实告知并尝试寻找答案
"""

# 创建agent
agent = create_agent(
    model=model,
    checkpointer=checkpointer,
    system_prompt=system_prompt,
    tools=[web_search]
)


# 流式对话
def search_recipes(prompt: str, image: str, thread_id: str):
    """调用agent搜索食谱"""
    logger.info(f"[用户]:{prompt},image:{image},thread_id:{thread_id}")
    
    # 检查环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        logger.error("DASHSCOPE_API_KEY 环境变量未设置")
        yield "抱歉，系统配置未完成，请联系管理员。"
        return
    
    # 判断是否有图片，封装不同格式的消息
    try:
        if not image or image.strip() == "":
            message = HumanMessage(content=prompt)
        else:
            message = HumanMessage(content=[
                {"type": "image", "url": image},
                {"type": "text", "text": prompt}
            ])
        
        # 获取历史消息，保持对话上下文
        history_messages = get_message(thread_id)
        
        # 将历史消息转换为 HumanMessage/AIMessage 对象
        messages = []
        for msg in history_messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # 添加新消息
        messages.append(message)
        
        # 调用agent（使用 checkpointer 来保存状态）
        config = {"configurable": {"thread_id": thread_id}}
        
        # 如果没有历史消息，使用新会话
        if not history_messages:
            logger.info("新会话，开始对话")
        else:
            logger.info(f"继续对话，历史消息数: {len(history_messages)}")
        
        # 调用 agent 流式响应（stream_mode="messages" 会自动保存）
        for chunk, metadata in agent.stream(
                {"messages": messages},
                config,
                stream_mode="messages"
        ):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                yield chunk.content
    except Exception as e:
        logger.error(f"\n[错误]:{str(e)}")
        # 提供更详细的错误信息
        error_msg = str(e)
        if "API key" in error_msg or "Unauthorized" in error_msg:
            yield "抱歉，API 密钥配置错误，请检查系统设置。"
        elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
            yield "抱歉，网络连接超时，请稍后重试。"
        else:
            yield f"抱歉，处理请求时发生错误: {error_msg[:50]}..."

# 清空对话
def clear_messages(thread_id: str):
    """清空会话"""
    logger.info(f"清空历史消息，thread_id:{thread_id}")
    checkpointer.delete_thread(thread_id)

# 获取所有会话列表
def get_all_threads()->list[dict[str, str]]:
    """获取所有会话列表"""
    logger.info("获取所有会话列表")
    
    # 使用 SQLite 直接查询所有线程
    conn = sqlite3.connect("./db/personal_agent.db", check_same_thread=False)
    cursor = conn.cursor()
    
    try:
        # 查询所有线程（支持不同的表结构）
        cursor.execute("SELECT key, value FROM checkpoints ORDER BY rowid DESC")
        rows = cursor.fetchall()
        
        result = []
        seen_threads = set()
        
        for row in rows:
            key = row[0]
            # 解析 thread_id
            if key.startswith("configurable/"):
                thread_id = key.replace("configurable/", "")
                if thread_id not in seen_threads:
                    seen_threads.add(thread_id)
                    
                    # 获取会话的第一条消息作为标题
                    messages = get_message(thread_id)
                    if messages:
                        first_message = str(messages[0].get("content", ""))
                        # 截取前30个字符作为标题
                        title = first_message[:30] + "..." if len(first_message) > 30 else first_message
                    else:
                        title = "空会话"
                    
                    result.append({
                        "thread_id": thread_id,
                        "title": title,
                        "created_at": ""
                    })
        
        return result
    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        return []
    finally:
        conn.close()

# 查询历史会话
def get_message(thread_id: str)->list[dict[str, str]]:
    """获取历史消息"""
    logger.info(f"获取历史消息:{thread_id}")

    try:
        # 根据thread_id 查询 checkpoint
        checkpoint=checkpointer.get({"configurable": {"thread_id": thread_id}})

        # 如果不存在。返回空列表
        if not checkpoint:
            logger.info("checkpoint 不存在")
            return []

        # 正确获取 messages（LangGraph 0.2+ 的格式）
        messages = []
        if isinstance(checkpoint, dict):
            channel_values = checkpoint.get("channel_values")
            if channel_values and isinstance(channel_values, dict):
                messages = channel_values.get("messages", [])
        
        # 如果不是预期格式，尝试其他方式
        if not messages and hasattr(checkpoint, '__getitem__'):
            try:
                messages = checkpoint["channel_values"].get("messages", [])
            except:
                pass

        if not messages:
            logger.info("messages 为空")
            return []

        # 转换消息格式
        result = []
        for message in messages:
            if not hasattr(message, 'content') or not message.content:
                continue

            if isinstance(message, HumanMessage):
                content = str(message.content)
                result.append({"role": "user", "content": content})
                
            elif isinstance(message, (AIMessageChunk, AIMessage)):
                content = str(message.content)
                result.append({"role": "assistant", "content": content})
        
        # 反转消息顺序，确保最新的消息在最后
        return result[::-1]
    except Exception as e:
        logger.error(f"获取历史消息失败: {str(e)}")
        return []

