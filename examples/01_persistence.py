#!/usr/bin/env python3
"""
扩展示例1: Persistence（持久化与记忆）

这个文件演示了如何让 Agent 拥有记忆，支持：
1. 多轮对话
2. 断点续聊
3. 查看历史状态（Time Travel）

运行方式:
    python examples/01_persistence.py
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
# 如果想持久化到文件，取消下面的注释：
# from langgraph.checkpoint.sqlite import SqliteSaver

from src.graph.state import State
from src.graph.nodes import planner_node, researcher_node, writer_node


def build_graph_with_memory():
    """构建带记忆的工作流"""
    builder = StateGraph(State)
    
    builder.add_node("planner", planner_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("writer", writer_node)
    
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "researcher")
    builder.add_edge("researcher", "writer")
    builder.add_edge("writer", END)
    
    # ========== 关键改动：添加 checkpointer ==========
    memory = MemorySaver()
    
    # 如果想持久化到 SQLite 文件：
    # memory = SqliteSaver.from_conn_string("checkpoints.db")
    
    return builder.compile(checkpointer=memory)


async def demo_multi_turn_conversation():
    """演示：多轮对话"""
    print("\n" + "="*60)
    print("📝 演示：多轮对话（使用同一个 thread_id）")
    print("="*60)
    
    graph = build_graph_with_memory()
    
    # 关键：使用 thread_id 来关联对话
    config = {"configurable": {"thread_id": "conversation-001"}}
    
    # 第一轮对话
    print("\n🔹 第一轮：询问 Python")
    result1 = await graph.ainvoke(
        {"messages": [], "task": "Python 是什么语言？", "plan": "", "research_results": "", "final_answer": ""},
        config
    )
    print(f"✅ 答案: {result1['final_answer'][:200]}...")
    
    # 第二轮对话 - 会记住之前的上下文！
    print("\n🔹 第二轮：追问（Agent 会记住上下文）")
    result2 = await graph.ainvoke(
        {"messages": [], "task": "它和 Java 有什么区别？", "plan": "", "research_results": "", "final_answer": ""},
        config
    )
    print(f"✅ 答案: {result2['final_answer'][:200]}...")
    
    # 查看消息历史
    state = graph.get_state(config)
    print(f"\n📊 消息历史数量: {len(state.values.get('messages', []))}")


async def demo_state_history():
    """演示：查看执行历史（Time Travel）"""
    print("\n" + "="*60)
    print("📝 演示：查看执行历史（Time Travel）")
    print("="*60)
    
    graph = build_graph_with_memory()
    config = {"configurable": {"thread_id": "history-demo"}}
    
    # 运行一次工作流
    await graph.ainvoke(
        {"messages": [], "task": "什么是机器学习？", "plan": "", "research_results": "", "final_answer": ""},
        config
    )
    
    # 获取所有历史状态
    print("\n🕐 执行历史：")
    history = list(graph.get_state_history(config))
    
    for i, state in enumerate(history):
        node = state.metadata.get('langgraph_node', 'START')
        step = state.metadata.get('step', 0)
        keys_with_content = [k for k, v in state.values.items() if v]
        print(f"  Step {step} | Node: {node:12} | 有数据的字段: {keys_with_content}")


async def demo_resume_conversation():
    """演示：断点续聊"""
    print("\n" + "="*60)
    print("📝 演示：断点续聊（模拟程序重启）")
    print("="*60)
    
    # 使用 SQLite 持久化（这样即使程序重启也能恢复）
    # 注意：这里用内存演示，实际使用请换成 SqliteSaver
    
    graph = build_graph_with_memory()
    config = {"configurable": {"thread_id": "resume-demo"}}
    
    # 第一次运行
    print("\n🔹 第一次运行...")
    await graph.ainvoke(
        {"messages": [], "task": "什么是深度学习？", "plan": "", "research_results": "", "final_answer": ""},
        config
    )
    
    # 模拟"程序重启" - 创建新的 graph 实例
    # 如果使用 SqliteSaver，状态会从数据库恢复
    print("\n🔹 模拟程序重启，创建新的 graph...")
    graph2 = build_graph_with_memory()
    
    # 检查状态是否还在（使用内存会丢失，使用 SQLite 会保留）
    state = graph2.get_state(config)
    if state and state.values:
        print("✅ 状态已恢复！")
        print(f"   之前的任务: {state.values.get('task', 'N/A')}")
    else:
        print("⚠️ 使用内存存储时，状态会丢失")
        print("   提示：使用 SqliteSaver 可以持久化到文件")


async def interactive_mode():
    """交互模式：体验多轮对话"""
    print("\n" + "="*60)
    print("🎮 交互模式：体验多轮对话")
    print("="*60)
    print("输入 'quit' 退出，输入 'history' 查看历史\n")
    
    graph = build_graph_with_memory()
    config = {"configurable": {"thread_id": "interactive-session"}}
    
    while True:
        user_input = input("你: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break
            
        if user_input.lower() == 'history':
            # 查看历史
            history = list(graph.get_state_history(config))
            print(f"\n📊 共 {len(history)} 个历史状态")
            for i, state in enumerate(history[:5]):  # 只显示最近5个
                node = state.metadata.get('langgraph_node', '?')
                print(f"  {i+1}. {node}")
            print()
            continue
            
        if not user_input:
            continue
        
        # 运行工作流
        print("\n🤔 思考中...")
        result = await graph.ainvoke(
            {"messages": [], "task": user_input, "plan": "", "research_results": "", "final_answer": ""},
            config
        )
        print(f"\n🤖 Agent: {result['final_answer']}\n")


async def main():
    """主函数"""
    print("🦌 LangGraph 扩展学习 - Persistence（持久化）")
    print("="*60)
    
    # 运行演示
    await demo_multi_turn_conversation()
    await demo_state_history()
    await demo_resume_conversation()
    
    # 可选：进入交互模式
    # await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
