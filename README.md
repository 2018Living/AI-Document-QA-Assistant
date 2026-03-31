markdown
# 📚 AI文档问答助手

一个基于智谱AI的智能文档问答工具，上传 PDF 或 TXT，AI 帮你回答文档里的问题。

## 功能
- ✅ 支持 PDF / TXT 文件上传
- ✅ 自动切分文档，关键词检索相关内容
- ✅ 对话记忆，可清除历史
- ✅ 侧边栏显示检索到的段落（调试用）

## 安装
```bash
pip install -r requirements.txt
运行
bash
streamlit run chat_app.py
环境变量
创建 .env 文件：

text
API_KEY=你的智谱API密钥
BASE_URL=https://open.bigmodel.cn/api/paas/v4/

## 📸 效果截图

![运行截图](images/screenshot.png)


技术栈
Python + Streamlit

智谱AI API (GLM-4-Flash)

RAG（检索增强生成）简化实现

作者
Lie Ying