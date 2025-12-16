#!/usr/bin/env python3
"""
扩展示例2: Human-in-the-Loop（人工介入）

这个文件演示了如何在关键步骤加入人工审核：
1. 在 writer 之前暂停
2. 人工审核研究结果
3. 选择：通过 / 拒绝 / 修改

运行方式:
    python examples/02_human_in_the_loop.py
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.graph.state import State
from src.graph.nodes import planner_node, researcher_node, writer_node


def build_graph_with_interrupt():
    """构建带人工审核断点的工作流"""
    builder = StateGraph(State)
    
    builder.add_node("planner", planner_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("writer", writer_node)
    
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "researcher")
    builder.add_edge("researcher", "writer")
    builder.add_edge("writer", END)
    
    memory = MemorySaver()
    
    # ========== 关键改动：设置断点 ==========
    return builder.compile(
        checkpointer=memory,
        interrupt_before=["writer"]  # 在进入 writer 之前暂停
        # 也可以用 interrupt_after=["researcher"] 在 researcher 之后暂停
    )


async def run_with_human_review(question: str):
    """运行带人工审核的工作流"""
    print("\n" + "="*60)
    print(f"📝 任务: {question}")
    print("="*60)
    
    graph = build_graph_with_interrupt()
    config = {"configurable": {"thread_id": f"review-{hash(question)}"}}
    
    initial_state = {
        "messages": [],
        "task": question,
        "plan": "",
        "research_results": "",
        "final_answer": ""
    }
    
    # 第一阶段：运行到断点
    print("\n🚀 开始执行 (会在 writer 前暂停)...\n")
    async for event in graph.astream(initial_state, config):
        for node_name in event:
            print(f"✅ [{node_name}] 完成")
    
    # 检查当前状态
    current_state = graph.get_state(config)
    
    # 如果 next 不为空，说明被中断了
    if current_state.next:
        print("\n" + "="*60)
        print("⏸️  工作流已暂停 - 等待人工审核")
        print("="*60)
        
        # 显示当前结果
        plan = current_state.values.get('plan', '')
        research = current_state.values.get('research_results', '')
        
        print(f"\n📋 研究计划:\n{'-'*40}")
        print(plan[:800] + "..." if len(plan) > 800 else plan)
        
        print(f"\n📚 研究结果:\n{'-'*40}")
        print(research[:800] + "..." if len(research) > 800 else research)
        
        # 人工审核界面
        print("\n" + "="*60)
        print("请选择操作:")
        print("  1. approve  - 通过，继续生成最终答案")
        print("  2. reject   - 拒绝，重新研究")
        print("  3. modify   - 添加修改意见后继续")
        print("  4. cancel   - 取消任务")
        print("="*60)
        
        choice = input("\n输入选项 (1/2/3/4): ").strip().lower()
        
        if choice in ['1', 'approve']:
            print("\n✅ 已通过，继续执行...")
            # 继续执行 - 传入 None 表示不修改状态
            async for event in graph.astream(None, config):
                for node_name in event:
                    print(f"✅ [{node_name}] 完成")
                    
        elif choice in ['2', 'reject']:
            print("\n🔄 已拒绝，重新研究...")
            # 清空研究结果，让 researcher 重新执行
            graph.update_state(
                config,
                {"research_results": "", "plan": "请换一个角度重新研究"},
                as_node="planner"  # 假装是 planner 输出的，这样会重新执行 researcher
            )
            async for event in graph.astream(None, config):
                for node_name in event:
                    print(f"✅ [{node_name}] 完成")
                    
        elif choice in ['3', 'modify']:
            feedback = input("\n请输入你的修改意见: ").strip()
            if feedback:
                # 把人类反馈追加到研究结果
                updated_research = f"{research}\n\n[人工补充说明]:\n{feedback}"
                graph.update_state(
                    config,
                    {"research_results": updated_research},
                    as_node="researcher"
                )
                print("\n✅ 已添加修改意见，继续执行...")
                async for event in graph.astream(None, config):
                    for node_name in event:
                        print(f"✅ [{node_name}] 完成")
            else:
                print("未输入意见，按原样继续...")
                async for event in graph.astream(None, config):
                    pass
                    
        else:
            print("\n❌ 已取消任务")
            return None
    
    # 获取最终结果
    final_state = graph.get_state(config)
    final_answer = final_state.values.get('final_answer', '')
    
    print("\n" + "="*60)
    print("📝 最终答案")
    print("="*60)
    print(final_answer)
    
    return final_state


async def demo_auto_approve():
    """演示：自动通过模式（用于测试）"""
    print("\n" + "="*60)
    print("📝 演示：自动通过模式")
    print("="*60)
    
    graph = build_graph_with_interrupt()
    config = {"configurable": {"thread_id": "auto-approve-demo"}}
    
    # 运行到断点
    result = None
    async for event in graph.astream(
        {"messages": [], "task": "什么是区块链？", "plan": "", "research_results": "", "final_answer": ""},
        config
    ):
        result = event
    
    # 检查是否被中断
    state = graph.get_state(config)
    if state.next:
        print(f"⏸️ 在 {state.next} 处暂停")
        print("✅ 自动通过...")
        
        # 自动继续
        async for event in graph.astream(None, config):
            result = event
    
    final = graph.get_state(config)
    print(f"\n结果: {final.values.get('final_answer', '')[:200]}...")


async def demo_modify_and_continue():
    """演示：修改状态后继续"""
    print("\n" + "="*60)
    print("📝 演示：修改状态后继续")
    print("="*60)
    
    graph = build_graph_with_interrupt()
    config = {"configurable": {"thread_id": "modify-demo"}}
    
    # 运行到断点
    async for event in graph.astream(
        {"messages": [], "task": "Python 的优点是什么？", "plan": "", "research_results": "", "final_answer": ""},
        config
    ):
        pass
    
    state = graph.get_state(config)
    if state.next:
        print(f"⏸️ 当前状态:")
        print(f"   plan: {state.values.get('plan', '')[:100]}...")
        
        # 修改状态
        print("\n🔧 修改研究结果，添加人工补充...")
        graph.update_state(
            config,
            {"research_results": state.values.get('research_results', '') + "\n\n[人工补充]: Python 非常适合初学者，语法简洁优雅。"},
            as_node="researcher"
        )
        
        # 继续执行
        print("▶️ 继续执行...")
        async for event in graph.astream(None, config):
            pass
    
    final = graph.get_state(config)
    print(f"\n最终答案: {final.values.get('final_answer', '')[:300]}...")


async def main():
    """主函数"""
    print("🦌 LangGraph 扩展学习 - Human-in-the-Loop（人工介入）")
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # 交互模式
        question = input("请输入你的问题: ").strip()
        if question:
            await run_with_human_review(question)
    else:
        # 演示模式
        await demo_auto_approve()
        await demo_modify_and_continue()
        
        print("\n" + "="*60)
        print("💡 提示：运行 `python examples/02_human_in_the_loop.py --interactive` 体验交互式审核")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
