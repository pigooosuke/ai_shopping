from assistant import create_assistant
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from models import State, Customer
from tools import fetch_customer_info, purchase_items, search_items


def _customer_info(state: State) -> dict[str, Customer]:
    """Customer情報を取得"""
    return {"customer_info": fetch_customer_info.invoke({})}


def _route_tools(state: State) -> str:
    """toolの分岐処理"""
    next_node = tools_condition(state)
    # ツールを呼び出してなければ会話終了
    if next_node == END:
        return END
    ai_message = state["messages"][-1]
    # 呼び出されたツールを取得
    first_tool_call = ai_message.tool_calls[0]
    if first_tool_call["name"] == "purchase_items":
        return "purchase_items"
    return "search_items"


def create_order_graph() -> CompiledStateGraph:
    """注文フローのグラフを構築"""
    workflow = StateGraph(State)

    # ノードの追加
    workflow.add_node("fetch_customer_info", _customer_info)
    workflow.add_node("assistant", create_assistant())
    workflow.add_node("search_items", ToolNode([search_items]))
    workflow.add_node("purchase_items", ToolNode([purchase_items]))
    # Define logic
    workflow.add_edge(START, "fetch_customer_info")
    workflow.add_edge("fetch_customer_info", "assistant")
    workflow.add_conditional_edges("assistant", _route_tools, ["search_items", "purchase_items", END])
    workflow.add_edge("search_items", "assistant")
    workflow.add_edge("purchase_items", "assistant")

    memory = MemorySaver()
    graph = workflow.compile(
        checkpointer=memory,
        interrupt_before=["purchase_items"],
    )

    return graph
