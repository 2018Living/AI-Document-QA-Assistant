import streamlit as st
import re
import pypdf
import os
from openai import OpenAI
from dotenv import load_dotenv
import logging
import sys

# ========== 加载环境变量 ==========
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'), # 写入文件
        logging.StreamHandler(sys.stdout) # 同时输出到终端
    ]
)
logger = logging.getLogger(__name__)

# ========== 函数定义 ==========
def split_text_into_chunks(text, chunk_size=500, overlap=100):
    """
    将文本切分成多个块
    chunk_size: 每块大约的字符数
    overlap: 块之间的重叠字符数（保持上下文连贯）
    """
    # 按句子分割（简单做法：按句号、问号、感叹号切分）
    sentences = re.split(r'[。！？!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # 如果当前块加上新句子不超过chunk_size，就加上
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence + "。"
        else:
            # 否则，保存当前块，开始新块
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence + "。"
    
    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def retrieve_relevant_chunks(query, chunks, top_k=3):
    """简化版：用关键词匹配检索相关chunks（不需要安装额外库）"""
    if not chunks:
        return []
    
    # 提取查询中的关键词（按空格和标点切分）
    query_words = set(re.findall(r'[\w\u4e00-\u9fff]+', query.lower()))
    
    # 计算每个chunk的关键词匹配分数
    scores = []
    for chunk in chunks:
        chunk_words = set(re.findall(r'[\w\u4e00-\u9fff]+', chunk.lower()))
        # 计算共同关键词数量
        common = query_words & chunk_words
        score = len(common)
        scores.append(score)
    
    # 获取分数最高的top_k个索引
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    
    # 只返回分数大于0的chunks
    relevant = [chunks[i] for i in top_indices if scores[i] > 0]
    return relevant if relevant else chunks[:top_k]


def read_file_content(uploaded_file):
    """根据文件类型读取内容，返回字符串"""
    try:
        file_type = uploaded_file.type
        
        if file_type == "text/plain":
            # 处理txt文件
            return uploaded_file.read().decode("utf-8")
        
        elif file_type == "application/pdf":
            # 处理PDF文件
            pdf_reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        
        else:
            return f"不支持的文件类型: {file_type}"
    except Exception as e:
        logger.error(f"读取文件失败：{e}")
        return f"文件读取失败：{str(e)}"

# ========== 初始化客户端 ==========
client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)

# ========== 页面标题 ==========
st.title("💬 我的第一个AI助手")
logger.info("应用启动")

# ========== 侧边栏：文件上传 ==========
st.sidebar.header("📁 文件上传")

uploaded_file = st.sidebar.file_uploader(
    "上传文件", 
    type=['txt', 'pdf'],
    help="支持txt和pdf格式"
)

# ========== 初始化 Session State ==========
if "file_content" not in st.session_state:
    st.session_state["file_content"] = ""

if "file_chunks" not in st.session_state:
    st.session_state["file_chunks"] = []

if "last_retrieved_chunks" not in st.session_state:
    st.session_state["last_retrieved_chunks"] = []

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": "你是一个智能助手。如果用户上传了文件，请根据文件内容回答问题。如果没上传文件，就正常聊天。你的回答要简洁、准确。"}]

# ========== 处理文件上传 ==========
if uploaded_file is not None:
    file_content = read_file_content(uploaded_file)
    st.session_state["file_content"] = file_content
    
    # 将文件内容切分成chunks
    chunks = split_text_into_chunks(file_content)
    st.session_state["file_chunks"] = chunks
    st.sidebar.success(f"已加载文件：{uploaded_file.name}，共{len(file_content)}字符，切分为{len(chunks)}个段落")
    
    # 显示文件预览
    with st.sidebar.expander("文件预览"):
        st.text(file_content[:500] + "..." if len(file_content) > 500 else file_content)

# ========== 调试区域：显示检索到的段落 ==========
if st.session_state.get("last_retrieved_chunks"):
    with st.sidebar.expander("🔍 调试：检索到的段落"):
        for i, chunk in enumerate(st.session_state["last_retrieved_chunks"]):
            st.text(f"段落{i+1}: {chunk[:200]}...")

# ========== 清除历史按钮 ==========
if st.button("🗑️ 清除对话历史"):
    st.session_state["messages"] = [{"role": "system", "content": "你是一个智能助手。如果用户上传了文件，请根据文件内容回答问题。如果没上传文件，就正常聊天。你的回答要简洁、准确。"}]
    st.rerun()

# ========== 显示对话轮数 ==========
if len(st.session_state.messages) > 1:
    st.caption(f"📝 当前对话轮数：{(len(st.session_state.messages)-1)//2} 轮")

# ========== 显示聊天记录 ==========
for msg in st.session_state.messages:
    if msg["role"] != "system":
        st.chat_message(msg["role"]).write(msg["content"])

# ========== 输入框 ==========
if prompt := st.chat_input("说点什么吧"):
    # 显示用户输入
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 准备要发送给AI的消息
    messages_to_send = st.session_state["messages"].copy()

    # ========== RAG：检索相关段落 ==========
    if st.session_state["file_chunks"]:
        # 获取用户最新问题
        user_query = None
        for msg in reversed(st.session_state["messages"]):
            if msg["role"] == "user":
                user_query = msg["content"]
                break

        if user_query:
            # 检索相关chunks
            relevant_chunks = retrieve_relevant_chunks(user_query, st.session_state["file_chunks"])
            
            # 保存到 session_state，供调试显示使用
            st.session_state["last_retrieved_chunks"] = relevant_chunks
            
            if relevant_chunks:
                # 构建上下文
                context = "\n\n---\n\n".join(relevant_chunks)
                rag_context = {
                    "role": "system",
                    "content": f"以下是从用户上传的文档中检索到的相关内容，请基于这些内容回答用户的问题。如果内容中没有相关信息，请告诉用户。\n\n{context}"  
                }
                # 插入到system消息之后
                messages_to_send.insert(1, rag_context)

    # ========== 调用AI ==========
    try:
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=messages_to_send,
            timeout=30 # 30秒超时，防止卡死
        )

        msg = response.choices[0].message.content

    except Exception as e:
        logger.error(f"AI调用失败: {e}")
        msg = f"抱歉，AI服务出了点问题：{str(e)}"
    
    # 显示回复
    st.chat_message("assistant").write(msg)
    st.session_state.messages.append({"role": "assistant", "content": msg})