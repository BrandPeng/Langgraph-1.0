# 🦌 从零开始构建多Agent项目

## **摒弃复杂的架构，回归 Agent 开发的本质**

## 项目简介

这是一个**最小化的多Agent项目模板**，帮助你理解 LangGraph 的核心概念，并快速上手开发自己的多Agent应用，仿照deer-flow做的demo项目，以更好的学习deer-flow。



---
## 📖 项目背景 (Why this project?)
许多优秀的开源项目虽然架构完善，但往往结构过于复杂。对于初学者而言，面对陌生的知识点和复杂的工程架构的双重挑战，往往很难理清核心逻辑。              

初学者真正需要关注的是项目的核心流程与关键知识点，而非宏大的架构设计，**复杂的工程结构往往掩盖了核心逻辑**。。

## 💡 项目目标 (Project Goal)
本项目旨在通过最精简的代码结构演示 LangGraph 的完整工作流。   
降低门槛：剥离非必要的封装，用最直观的接口展示 Agent 运行机制。    
快速上手：帮助初学者快速掌握 LangGraph 的核心概念与 Agent 开发流程。        
承上启下：为您阅读更复杂的开源项目打下基础，或作为脚手架构建属于自己的应用。     

## 📁 项目结构

```
my-agent-project/
│
├── main.py                 # 主入口
├── pyproject.toml          # 依赖配置
├── .env.example            # 环境变量示例
│
└── src/
    ├── graph/              # 核心：工作流定义
    │   ├── state.py        # 状态定义
    │   ├── nodes.py        # 节点（Agent）实现
    │   └── builder.py      # 图构建器
    │
    ├── prompts/            # 提示词
    │   ├── planner.md      # 规划器提示词
    │   ├── researcher.md   # 研究员提示词
    │   └── writer.md       # 写作者提示词
    │
    └── tools/              # 工具
        └── tools.py        # 搜索、计算等工具
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

### 3. 运行

```bash
# 直接提问
python main.py "什么是机器学习？"

# 交互模式
python main.py --interactive
```

---

## 🎯 核心概念详解

### 1️⃣ State（状态）

**状态就像一个共享的笔记本**，所有 Agent 都可以读写。

```python
# src/graph/state.py

class State(TypedDict):
    messages: list           # 对话历史
    task: str               # 用户任务
    plan: str               # 研究计划
    research_results: str   # 研究结果
    final_answer: str       # 最终答案
```

**关键点：**
- 每个字段都可以被任何节点读取
- 节点返回的字典会**合并**到状态中
- `Annotated[list, add_messages]` 表示消息会追加而不是覆盖

---

### 2️⃣ Node（节点）

**节点就是一个处理函数**，代表一个 Agent。

```python
# src/graph/nodes.py

def planner_node(state: State) -> dict:
    # 1. 读取状态
    task = state["task"]
    
    # 2. 调用 LLM
    response = llm.invoke(messages)
    
    # 3. 返回状态更新
    return {
        "plan": response.content,
        "messages": [response]
    }
```

**关键点：**
- 输入是完整的 State
- 输出是要更新的字段（字典）
- 只返回需要更新的字段即可

---

### 3️⃣ Graph（图）

**图定义了节点之间的连接关系**。

```python
# src/graph/builder.py

def build_graph():
    builder = StateGraph(State)
    
    # 添加节点
    builder.add_node("planner", planner_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("writer", writer_node)
    
    # 添加边（定义流程）
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "researcher")
    builder.add_edge("researcher", "writer")
    builder.add_edge("writer", END)
    
    return builder.compile()
```

**执行流程：**
```
START → planner → researcher → writer → END
```

---

### 4️⃣ Tool（工具）

**工具让 Agent 能与外部世界交互**。

```python
# src/tools/tools.py

@tool
def web_search(query: str) -> str:
    """搜索网络获取信息"""
    # 实现搜索逻辑
    return search_results
```

**绑定工具到 LLM：**
```python
llm_with_tools = llm.bind_tools([web_search, calculator])
response = llm_with_tools.invoke(messages)

# 如果 LLM 想调用工具
if response.tool_calls:
    for tool_call in response.tool_calls:
        result = tool.invoke(tool_call["args"])
```

---

## 🔧 如何扩展

### 添加新的 Agent

1. **创建提示词** `src/prompts/new_agent.md`
2. **实现节点函数** 在 `src/graph/nodes.py`
3. **添加到图中** 在 `src/graph/builder.py`

```python
# nodes.py
def new_agent_node(state: State) -> dict:
    # 你的逻辑
    return {"new_field": result}

# builder.py
builder.add_node("new_agent", new_agent_node)
builder.add_edge("researcher", "new_agent")
builder.add_edge("new_agent", "writer")
```

---

### 添加条件分支

```python
def decide_next(state: State) -> str:
    """根据状态决定下一步"""
    if needs_more_research(state):
        return "researcher"
    else:
        return "writer"

builder.add_conditional_edges(
    "researcher",
    decide_next,
    {"researcher": "researcher", "writer": "writer"}
)
```

---

### 添加新工具

```python
# src/tools/tools.py

@tool
def my_new_tool(param: str) -> str:
    """工具描述 - LLM 会根据这个描述决定何时使用"""
    # 实现逻辑
    return result

# 在 researcher_node 中使用
tools = [web_search, my_new_tool]
llm_with_tools = llm.bind_tools(tools)
```

---

## 📊 与 DeerFlow 的对比

| 方面 | 本模板 | DeerFlow |
|------|--------|----------|
| 复杂度 | 简单（3个Agent） | 复杂（5+个Agent） |
| 功能 | 基础研究 | 完整研究+播客+PPT |
| 学习曲线 | 平缓 | 陡峭 |
| 适用场景 | 学习/小项目 | 生产级应用 |

---

## 🎓 学习路径

1. **运行项目** - 先跑起来看效果
2. **修改提示词** - 改变 Agent 行为
3. **添加工具** - 扩展 Agent 能力
4. **添加 Agent** - 增加新角色
5. **添加条件分支** - 实现复杂逻辑
6. **参考 DeerFlow** - 学习高级用法

---

## 🚀 后续扩展学习 (Next Steps)   
当你跑通并理解项目后，建议按照以下顺序进阶，将项目从“Demo”升级为“生产级应用”：

1. **Persistence (持久化与记忆)**   
目标：让 Agent 拥有记忆，支持多轮对话和状态回滚。    
现状：目前程序运行结束后，所有状态（State）都会丢失。     
改进：

- 引入 Checkpointer（如 SqliteSaver 或 PostgresSaver）。

- 在编译图时使用 workflow.compile(checkpointer=memory)。

- 调用时传入 thread_id，系统会自动加载之前的聊天记录。   

进阶玩法：利用持久化实现 Time Travel（时间旅行），可以查看历史步骤的 State，甚至修改中间状态来纠正 Agent 的错误。    

2. **Human-in-the-loop (人工介入)**   
目标：在关键步骤加入人工审核，防止 Agent“胡说八道”。   
场景：在 Writer 生成最终文章前，暂停程序，让人类确认或修改内容。    
实现：
- 使用 interrupt_before=["writer"] 设置断点。
- 程序暂停后，用户可以输入指令：approve（通过）或 update_state（修改反馈）。
- 这是一个非常强大的功能，也是 LangGraph 区别于其他框架的核心优势。

3. **Agentic RAG (工具化检索增强)**   
目标：让 Agent 能够查询本地的私有文档（如 PDF、Markdown），而不仅仅是搜索互联网。   
思路：不要把 RAG 写成一个死板的 Chain，而是把它封装成一个 Tool。    
实现：
- 使用 LangChain 加载文档并存入向量数据库（如 Chroma）。
- 创建一个 retriever_tool，命名为 search_local_knowledge。
- 将这个工具绑定给 Researcher Agent。
- 效果：Agent 会根据问题自动判断是去“搜谷歌”还是“查本地文档”。


## ❓ 常见问题

### Q: 为什么要用多个 Agent？
**A:** 分工协作，每个 Agent 专注一件事，更容易调试和优化。

### Q: 状态太大会怎样？
**A:** 会消耗更多 token。可以在节点中清理不需要的字段。

### Q: 如何调试？
**A:** 
1. 在节点中添加 print 语句
2. 使用 LangGraph Studio 可视化
3. 启用 LangSmith 追踪

---

## 📚 参考资源

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [LangChain 官方文档](https://python.langchain.com/)
- [DeerFlow 项目](https://github.com/bytedance/deer-flow)

---

祝你开发顺利！🎉
