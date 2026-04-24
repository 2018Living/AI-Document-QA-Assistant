import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import sys

# ========== 加载环境变量 ==========
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ========== 初始化 FastAPI ==========
app = FastAPI(title="AI文档问答API", description="基于智谱AI的文档问答服务")
logger.info("FastAPI 服务启动")

# ========== 初始化 OpenAI 客户端 ==========
client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)

# ========== 定义请求和响应模型 ==========
class QuestionRequest(BaseModel):
    """用户提问的请求格式"""
    question: str
    context: Optional[str] = None  # 可选上下文

class AnswerResponse(BaseModel):
    """AI回答的响应格式"""
    answer: str
    status: str  # success 或 error

# ========== 关键词检索函数（从 chat_app.py 复用）==========
def extract_keywords(text: str) -> set:
    """提取中英文关键词"""
    # 方案一：在中文和英文/数字之间加一个虚拟分隔符，强制拆分
    import re
    # 在中文和英文/数字之间插入空格
    text = re.sub(r'([\u4e00-\u9fff])([a-zA-Z0-9])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z0-9])([\u4e00-\u9fff])', r'\1 \2', text)
    return set(re.findall(r'[\w\u4e00-\u9fff]+', text.lower()))

def retrieve_relevant_chunks(query: str, chunks: List[str], top_k: int = 3) -> List[str]:
    """根据关键词匹配检索相关段落"""
    if not chunks:
        return[]
    
    query_words = extract_keywords(query)
    scores = []
    for chunk in chunks:
        chunk_words = extract_keywords(chunk)
        common = query_words & chunk_words
        scores.append(len(common))

    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    relevant = [chunks[i] for i in top_indices if scores[i] > 0]
    return relevant if relevant else chunks[:top_k]

# ========== API 接口 ==========
@app.get("/")
def root():
    """根路径，检查服务是否运行"""
    return{"message": "AI文档问答API已启动", "status": "running"}

@app.get("/ask", response_model=AnswerResponse)
def ask_question(question: str, context: Optional[str] = None):
    """
    提问接口
    接收用户问题，返回AI回答
    """
    logger.info(f"收到提问：{question}")
    try:
        # 构建消息
        messages = [
            # {"role": "system", "content": "你是一个智能助手，请简洁准确地回答问题。"},
            # {"role": "system", "content": "你是一个幽默风趣的助手，喜欢用比喻和轻松的语气回答问题，但信息要准确。"},
            {"role": "system", "content": "你是一个鼓励者的角色，用户问什么你都先肯定对方，然后用简单易懂的方式回答"},
            {"role": "user", "content": question}
        ]
        
        if context:
            messages[0]["content"] += f"\n\n参考以下内容回答问题：\n{context}"

        # 调用AI
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=messages,
            timeout=30
        )

        answer = response.choices[0].message.content
        logger.info(f"AI 回答成功，长度：{len(answer)}字符")
        return AnswerResponse(answer=answer, status="success")           

    except Exception as e:
        logger.error(f"AI 调用失败：{e}")
        return AnswerResponse(answer=f"服务出错： {str(e)}", status="error")

# ========== 健康检查 ==========
@app.get("/health")
def health_check():
    return {"status": "ok"}


