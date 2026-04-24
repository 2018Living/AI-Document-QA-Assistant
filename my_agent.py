import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_tavily import TavilySearch

load_dotenv()

# ========== 定义工具 ==========
@tool
def calculate(expression: str) -> str:
    """计算数学表达式，例如 '123 * 456'"""
    try:
        result = eval(expression)
        return f"计算结果：{result}"
    except Exception as e:
        return f"计算错误：{e}"

@tool
def get_current_time() -> str:
    """获取当前时间。不需要任何参数。"""
    from datetime import datetime
    import pytz
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 创建真实的搜索工具
tavily_tool = TavilySearch(
    max_results=3,
    topic="general",
    include_answer=True,  # 包含 AI 总结的答案
)

# ========== 创建 Agent ==========
def create_agent():
    # 初始化 LLM
    llm = ChatOpenAI(
        model="glm-4-flash",
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("BASE_URL"),
        temperature=0
    )
    
    tools = [calculate, get_current_time, tavily_tool]
    
    # 绑定工具到 LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # 定义应该调用哪个工具
    def should_continue(state: MessagesState):
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END
    
    # 调用模型
    def call_model(state: MessagesState):
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    # 构建图
    workflow = StateGraph(MessagesState)
    
    # 添加节点
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    
    # 添加边
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")
    
    # 编译
    app = workflow.compile()
    
    return app

# ========== 运行测试 ==========
if __name__ == "__main__":
    app = create_agent()
    
    print("=" * 50)
    print("AI Agent 测试")
    print("=" * 50)
    
    # 测试1：计算
    print("\n【测试1】用户：计算 123 * 456")
    inputs = {"messages": [HumanMessage(content="计算 123 * 456")]}
    for event in app.stream(inputs, stream_mode="values"):
        event["messages"][-1].pretty_print()
    
    # 测试2：时间
    print("\n【测试2】用户：现在几点了？")
    inputs = {"messages": [HumanMessage(content="现在几点了？")]}
    for event in app.stream(inputs, stream_mode="values"):
        event["messages"][-1].pretty_print()
    
    # 测试3：搜索
    print("\n【测试3】用户：搜索一下最新的AI新闻")
    inputs = {"messages": [HumanMessage(content="搜索一下最新的AI新闻")]}
    for event in app.stream(inputs, stream_mode="values"):
        event["messages"][-1].pretty_print()