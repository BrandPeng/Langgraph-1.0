"""
节点定义 - 每个 Agent 的具体实现

每个节点就是一个函数：
- 输入: State (当前状态)
- 输出: dict (要更新的状态字段)
"""

import os
from pathlib import Path

from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from .state import State
from ..tools.tools import get_research_tools


# ============================================================
# 辅助函数
# ============================================================

## 读取模型api 选择自己的模型 这里用的是百炼平台提供的大模型api
ALIBABA_BASE_URL = os.environ.get("ALIBABA_BASE_URL")
ALIBABA_API_KEY = os.getenv("ALIBABA_API_KEY")
model = init_chat_model(
    "deepseek-v3",  # 1. 模型名称：请在百炼控制台确认准确的 model ID
    model_provider="openai",  # 2. 提供商：必须填 openai
    base_url= ALIBABA_BASE_URL,  # 3. 地址：百炼的兼容入口
    api_key=ALIBABA_API_KEY,  # 4. 你的百炼 API Key
)


def load_prompt(name: str) -> str:
    """加载提示词文件"""
    prompt_path = Path(__file__).parent.parent / "prompts" / f"{name}.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return ""


# ============================================================
# 节点实现
# ============================================================

def planner_node(state: State) -> dict:
    """
    规划器节点 - 制定研究计划
    
    输入: 用户的任务
    输出: 执行计划
    """
    print("\n🎯 [规划器] 正在制定计划...")
    
    llm = model
    system_prompt = load_prompt("planner")
    
    # 构建消息
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"请为以下任务制定研究计划：\n\n{state['task']}")
    ]
    
    # 调用 LLM
    response = llm.invoke(messages)
    plan = response.content
    
    print(f"📋 计划已生成:\n{plan}\n")
    
    # 返回要更新的状态
    return {
        "plan": plan,
        "messages": [response]
    }


def researcher_node(state: State) -> dict:
    """
    研究员节点 - 搜索和收集信息
    
    输入: 执行计划
    输出: 研究结果
    """
    print("\n🔍 [研究员] 正在收集信息...")
    
    llm = model
    system_prompt = load_prompt("researcher")
    
    # 绑定工具到 LLM
    tools = get_research_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    # 构建消息
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"""
任务: {state['task']}

研究计划:
{state['plan']}

请根据计划搜索相关信息。
""")
    ]
    
    # 第一次调用 - LLM 决定是否使用工具
    response = llm_with_tools.invoke(messages)

    # 如果 LLM 想要调用工具
    if response.tool_calls:
        print(f"🔧 调用工具: {[tc['name'] for tc in response.tool_calls]}")

        # 先把 assistant 的响应加入消息列表
        messages.append(response)

        # 执行每个工具调用，并用 ToolMessage 返回结果
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]  # 获取 tool_call_id

            # 找到并执行对应的工具
            result = "工具未找到"
            for tool in tools:
                if tool.name == tool_name:
                    result = tool.invoke(tool_args)
                    break

            # 使用 ToolMessage 返回结果（必须指定 tool_call_id）
            messages.append(ToolMessage(
                content=str(result),
                tool_call_id=tool_call_id
            ))

        # 让 LLM 整理工具返回的结果
        response = llm.invoke(messages)
    
    research_results = response.content
    print(f"📚 研究完成，收集到信息\n")
    
    return {
        "research_results": research_results,
        "messages": [response]
    }


def writer_node(state: State) -> dict:
    """
    写作者节点 - 生成最终答案
    
    输入: 研究结果
    输出: 最终答案
    """
    print("\n✍️ [写作者] 正在撰写答案...")
    
    llm = model
    system_prompt = load_prompt("writer")
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"""
用户问题: {state['task']}

研究结果:
{state['research_results']}

请根据以上研究结果，撰写一份完整的回答。
""")
    ]
    
    response = llm.invoke(messages)
    final_answer = response.content
    
    print(f"✅ 答案已生成\n")
    
    return {
        "final_answer": final_answer,
        "messages": [response]
    }
