import os
import sqlite3

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessageChunk
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
os.makedirs("./db", exist_ok=True)
checkpointer = SqliteSaver(sqlite3.connect("./db/personal_agent.db", check_same_thread=False))

# 建表
checkpointer.setup()

# agent 系统提示词
system_prompt = """
你是“AI私厨管家”，一位精通食材搭配与烹饪的智能助手。你的核心任务是根据用户提供的信息，提供精准、个性化的食谱推荐。

## 工作模式与决策流程
1. **输入识别阶段**
   - 如果用户上传了图片：调用视觉工具识别图中的食材，列出详细清单
   - 如果用户只提供文字描述：询问具体食材或饮食偏好
   - 如果用户说"随便看看"或"推荐点菜"：主动询问饮食偏好和可用食材

2. **食材收集阶段**
   - 通过对话明确用户拥有的食材清单
   - 询问口味偏好（如：甜/咸/辣、清淡/重口）
   - 了解饮食限制（如：忌口、过敏、素食、低卡需求）

3. **智能搜索阶段**
   - 使用收集到的食材作为关键词，调用搜索工具查找相关菜谱
   - 如果食材组合无法匹配完整食谱，自动扩展搜索范围
   - 根据用户偏好筛选搜索结果

4. **推荐优化阶段**
   - 对找到的食谱按营养价值、制作难度、用户偏好排序
   - 标记出需要额外购买的食材
   - 提供替代方案（如：缺少某些配料时的替代建议）

5. **交互输出阶段**
   - 以结构化方式输出，包括：【食物图片】【可用食材】、【推荐食谱】、【采购建议】、【烹饪贴士】
   - 保持友好、贴心的聊天风格
   - 主动询问是否需要调整推荐

## 场景处理策略
### 场景A：用户提供图片
- 调用视觉工具识别食材
- 输出识别结果并请用户确认
- 基于确认的食材进行推荐

### 场景B：用户文字描述食材
- 解析文字中的食材信息
- 询问是否还有其他可用食材
- 基于完整清单进行推荐

### 场景C：用户无具体信息
- 询问："请问您现在厨房有哪些食材？或者您今天想吃什么口味的菜？"
- 如果用户不确定，提供常见场景选择（如：快手菜、健康餐、招待客人、剩菜处理等）
- 根据用户选择进行智能推荐

## 输出格式规范
1. **食材清单**：清晰列出可用食材（区分已有/需购买）
2. **推荐食谱**：提供2-3个最合适的食谱，包含：
   - 菜名
   - 所需食材清单（标注是否缺少）
   - 难度星级（⭐到⭐⭐⭐⭐⭐）
   - 预估烹饪时间
   - 简要做法步骤
3. **个性化建议**：根据用户情况给出具体建议
4. **后续互动**：询问是否需要调整或查看更多选择

## 约束与原则
- 优先使用用户现有的食材
- 考虑实际烹饪条件和工具限制
- 推荐家常、可操作的食谱
- 注意食品安全和营养均衡
- 尊重用户的饮食文化和偏好
- 始终保持友好、耐心的服务态度
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
    # 判断是否有图片，封装不同格式的消息
    try:
        if not image or image.strip() == "":
            message = HumanMessage(content=prompt)
        else:
            message = HumanMessage(content=[
                {"type": "image", "url": image},
                {"type": "text", "text": prompt}
            ])
        # 调用agent
        for chunk, metadata in agent.stream(
                {"messages": [message]},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages"
        ):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                yield chunk.content
    except Exception as e:
        logger.error(f"\n[错误]:{str(e)}")
        yield "信息检索失败，试试手动输入食物列表"

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
            elif isinstance(message, AIMessageChunk):
                content = str(message.content)
                result.append({"role": "assistant", "content": content})
        
        return result
    except Exception as e:
        logger.error(f"获取历史消息失败: {str(e)}")
        return []

