#!/usr/bin/env python3
"""
我的多Agent项目 - 主入口

使用方法:
    python main.py "你的问题"
    python main.py --interactive
"""

import argparse
import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from src.graph import build_graph


async def run_workflow(question: str):
    """
    运行多Agent工作流
    
    Args:
        question: 用户的问题
    """
    print("=" * 60)
    print(f"🦌 开始处理问题: {question}")
    print("=" * 60)
    
    # 构建图
    graph = build_graph()
    
    # 初始状态
    initial_state = {
        "messages": [],
        "task": question,
        "plan": "",
        "research_results": "",
        "final_answer": ""
    }
    
    # 运行工作流
    final_state = None
    async for state in graph.astream(initial_state):
        final_state = state
    
    # 输出最终答案
    print("\n" + "=" * 60)
    print("📝 最终答案")
    print("=" * 60)
    
    # 获取最终答案
    if final_state and "writer" in final_state:
        answer = final_state["writer"].get("final_answer", "")
        print(answer)
    
    return final_state


def run_sync(question: str):
    """同步运行工作流"""
    return asyncio.run(run_workflow(question))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="我的多Agent研究助手")
    parser.add_argument("question", nargs="*", help="要研究的问题")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互模式")
    
    args = parser.parse_args()
    
    if args.interactive:
        # 交互模式
        print("🦌 欢迎使用多Agent研究助手！")
        print("输入 'quit' 或 'exit' 退出\n")
        
        while True:
            question = input("请输入你的问题: ").strip()
            if question.lower() in ["quit", "exit", "q"]:
                print("再见！👋")
                break
            if not question:
                continue
            
            run_sync(question)
            print("\n")
    else:
        # 命令行模式
        if args.question:
            question = " ".join(args.question)
        else:
            question = input("请输入你的问题: ").strip()
        
        if question:
            run_sync(question)


if __name__ == "__main__":
    main()
