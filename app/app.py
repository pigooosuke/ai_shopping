from logging import getLogger
import random
from uuid import uuid4

import chainlit as cl
from langchain_core.messages import HumanMessage, AIMessage
from models import State
from workflows import create_order_graph
from langchain_core.runnables import RunnableConfig
from handler import OrderProcessHandler

logger = getLogger(__name__)


def get_random_book_image() -> cl.Image:
    img_id = random.randint(1, 4)
    return cl.Image(path=f"./imgs/book_{img_id}.png", name="image_{img_id}", display="inline")


@cl.on_chat_start
async def start():
    WELCOME_MESSAGE = """
        こんにちは！
        当店は幅広いジャンルの書籍を取り扱っております。どのようなものをお探しでしょうか？
    """
    cl.user_session.set("state", State(messages=[]))
    cl.user_session.set("workflow", create_order_graph())
    cl.user_session.set("thread_id", str(uuid4()))
    await cl.Message(content=WELCOME_MESSAGE).send()


@cl.on_message
async def on_message(message: cl.Message):
    state = cl.user_session.get("state")
    workflow = cl.user_session.get("workflow")
    config = RunnableConfig({"configurable": {"thread_id": cl.user_session.get("thread_id")}})

    # メッセージを状態に追加
    state["messages"].append(HumanMessage(content=message.content))
    try:
        # ワークフロー実行
        result = await workflow.ainvoke(state, config)
        last_message = result["messages"][-1]

        # purchase_itemsが呼び出された場合
        if isinstance(last_message, AIMessage) and any(
            call["function"]["name"] == "purchase_items"
            for call in getattr(last_message, "additional_kwargs", {}).get("tool_calls", [])
        ):
            order_processor = OrderProcessHandler(state, workflow, config, state["messages"])
            # 購入意思を確認する
            purchase_result = await order_processor.process_purchase_confirmation(last_message)
            if purchase_result and purchase_result["messages"]:
                await cl.Message(content=purchase_result["messages"][-1].content).send()
        # 通常の応答
        else:
            await cl.Message(content=result["messages"][-1].content).send()
        cl.user_session.set("state", state)

    except Exception as e:
        logger.error(f"Error: {e}")
        await cl.Message(content=f"申し訳ございません。エラーが発生しました: {str(e)}").send()
