"""
图构建器 - 定义多Agent工作流

这是整个项目的"总控"，定义了：
1. 有哪些节点（Agent）
2. 它们之间如何连接
3. 执行顺序是什么
"""

from langgraph.graph import StateGraph, START, END

from .state import State
from .nodes import planner_node, researcher_node, writer_node


def build_graph():
    """
    构建并返回工作流图
    
    工作流程:
    START -> planner -> researcher -> writer -> END
    
    可以根据需要添加：
    - 条件分支 (add_conditional_edges)
    - 循环 (边指回之前的节点)
    - 并行执行 (多个边从同一节点出发)
    """
    
    # 1. 创建状态图，传入状态类型
    builder = StateGraph(State)
    
    # 2. 添加节点 - 每个节点是一个处理函数
    builder.add_node("planner", planner_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("writer", writer_node)
    
    # 3. 添加边 - 定义执行顺序
    builder.add_edge(START, "planner")        # 开始 -> 规划器
    builder.add_edge("planner", "researcher")  # 规划器 -> 研究员
    builder.add_edge("researcher", "writer")   # 研究员 -> 写作者
    builder.add_edge("writer", END)            # 写作者 -> 结束
    
    # 4. 编译图
    graph = builder.compile()
    
    return graph


def build_graph_with_condition():
    """
    带条件分支的工作流示例
    
    这个示例展示了如何根据条件选择不同的路径
    """
    
    def should_continue_research(state: State) -> str:
        """
        条件函数 - 决定是否需要继续研究
        
        返回下一个节点的名称
        """
        # 示例：如果研究结果太短，继续研究
        if len(state.get("research_results", "")) < 100:
            return "researcher"  # 返回研究员继续研究
        else:
            return "writer"      # 进入写作阶段
    
    builder = StateGraph(State)
    
    builder.add_node("planner", planner_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("writer", writer_node)
    
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "researcher")
    
    # 条件边 - 根据函数返回值选择下一个节点
    builder.add_conditional_edges(
        "researcher",           # 从哪个节点出发
        should_continue_research,  # 条件判断函数
        {
            "researcher": "researcher",  # 继续研究
            "writer": "writer"           # 进入写作
        }
    )
    
    builder.add_edge("writer", END)
    
    return builder.compile()


# 默认图
graph = build_graph()
