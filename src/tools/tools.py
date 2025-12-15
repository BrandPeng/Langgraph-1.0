"""
工具定义 - Agent 可以调用的外部能力

工具让 Agent 能够与外部世界交互，比如搜索网络、执行代码等。
"""

import os
from langchain_core.tools import tool


@tool
def web_search(query: str) -> str:
    """
    搜索网络获取信息。
    
    Args:
        query: 搜索关键词
        
    Returns:
        搜索结果摘要
    """
    # 检查是否配置了 Tavily API
    api_key = os.getenv("TAVILY_API_KEY")
    
    if api_key:
        # 使用 Tavily 搜索
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=api_key)
            response = client.search(query, max_results=5)
            
            # 格式化结果
            results = []
            for item in response.get("results", []):
                results.append(f"**{item['title']}**\n{item['content']}\n来源: {item['url']}\n")
            
            return "\n---\n".join(results) if results else "未找到相关结果"
        except Exception as e:
            return f"搜索出错: {str(e)}"
    else:
        # 没有配置 API，返回模拟结果
        return f"""
[模拟搜索结果 - 请配置 TAVILY_API_KEY 以获取真实结果]

搜索词: {query}

模拟结果1: 这是关于 {query} 的第一条搜索结果...
模拟结果2: 这是关于 {query} 的第二条搜索结果...
模拟结果3: 这是关于 {query} 的第三条搜索结果...
"""


@tool  
def calculator(expression: str) -> str:
    """
    计算数学表达式。
    
    Args:
        expression: 数学表达式，如 "2 + 2" 或 "100 * 0.15"
        
    Returns:
        计算结果
    """
    try:
        # 安全地计算表达式
        # 注意：eval 在生产环境中需要更严格的安全措施
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "错误：表达式包含非法字符"
        
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


# 导出所有工具
def get_research_tools():
    """获取研究员可用的工具列表"""
    return [web_search]


def get_all_tools():
    """获取所有可用工具"""
    return [web_search, calculator]
