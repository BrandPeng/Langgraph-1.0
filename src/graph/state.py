"""
状态定义 - 所有Agent共享的数据结构

State 就像一个"共享白板"，所有Agent都可以读写。
当一个Agent完成任务后，它的输出会写入State，供下一个Agent使用。
"""

from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class State(TypedDict):
    """
    工作流状态 - 在所有节点之间共享
    
    Attributes:
        messages: 对话历史，使用 add_messages 自动合并新消息
        task: 用户的原始任务/问题
        plan: 规划器生成的执行计划
        research_results: 研究员收集的信息
        final_answer: 最终输出给用户的答案
    """
    
    # 对话历史 - Annotated[..., add_messages] 表示新消息会追加而不是覆盖
    messages: Annotated[list, add_messages]
    
    # 用户任务
    task: str
    
    # 执行计划 (由 Planner 生成)
    plan: str
    
    # 研究结果 (由 Researcher 收集)
    research_results: str
    
    # 最终答案 (由 Writer 生成)
    final_answer: str
