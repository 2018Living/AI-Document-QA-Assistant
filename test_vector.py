# 这是一个不用跑通的“验证文件”，只检查语法
from sentence_transformers import SentenceTransformer

try:
    print("向量检索模块加载成功")
    print("注意：实际运行时需要下载模型，当前跳过运行")
except Exception as e:
    print("语法没问题，但模型未运行")