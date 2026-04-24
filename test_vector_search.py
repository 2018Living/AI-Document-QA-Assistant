import chromadb
from sentence_transformers import SentenceTransformer

# 1. 初始化向量数据库（使用内存模式）
client = chromadb.Client()
collection = client.create_collection(name="test_docs")

# 2. 初始化 embedding 模型（将文字转成向量）
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# 3. 准备测试文档
documents = [
    "Python是一种编程语言",
    "今天天气很好",
    "Docker是容器化工具"
]

# 4. 将文档转换成向量并存入 Chroma
embeddings = model.encode(documents).tolist()
collection.add(
    ids=["doc1", "doc2", "doc3"],
    documents=documents,
    embeddings=embeddings
)

# 5. 搜索：查询"编程"，找出最相关的文档
query = "编程"
query_embedding = model.encode([query]).tolist()
results = collection.query(query_embeddings=query_embedding, n_results=2)

print("查询结果：", results['documents'][0])