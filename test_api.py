import pytest
from api import extract_keywords, retrieve_relevant_chunks

# ========== 测试 extract_keywords 函数 ==========
def test_extract_keywords_basic():
    """测试：基本的中英文关键词提取"""
    result = extract_keywords("Python是一种编程语言")
    assert "python" in result
    assert "编程语言" in result

def test_extract_keywords_empty():
    """测试：空字符串返回空集合"""
    result = extract_keywords("")
    assert result == set()

def test_extract_keywords_mixed():
    """测试：中英文混合、大小写转换"""
    result = extract_keywords("Hello 世界 123")
    assert "hello" in result
    assert "世界" in result
    assert "123" in result

# ========== 测试 retrieve_relevant_chunks 函数 ==========
def test_retrieve_relevant_chunks_basic():
    """测试：能正确检索相关段落"""
    chunks = [
        "Python是一种编程语言",
        "今天天气很好",
        "Docker是容器化工具"
    ]
    result = retrieve_relevant_chunks("Python", chunks)
    assert result == ["Python是一种编程语言"]

def test_retrieve_relevant_chunks_no_match():
    """测试：没有匹配时，返回前 top_k 个段落"""
    chunks = ["苹果好吃", "香蕉好吃", "橘子好吃"]
    result = retrieve_relevant_chunks("Python", chunks)
    # 没有匹配，返回前3个
    assert len(result) == 3
    assert result == chunks

def test_retrieve_relevant_chunks_top_k():
    """测试：top_k 参数生效"""
    chunks = ["苹果", "香蕉", "橘子", "葡萄"]
    result = retrieve_relevant_chunks("水果", chunks, top_k=2)
    # 没有精确匹配，返回前2个
    assert len(result) == 2