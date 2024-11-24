import uuid
import json
from logging import getLogger
import random

import chainlit as cl
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from models import State
from langchain_core.tools import tool
from workflows import create_order_graph
from tools import purchase_items

logger = getLogger(__name__)


def get_img() -> cl.Image:
    img_id = random.randint(1, 4)
    return cl.Image(path=f"./imgs/book_{img_id}.png", name="image_{img_id}", display="inline")


@cl.on_chat_start
async def start():
    cl.user_session.set("state", State(messages=[]))
    cl.user_session.set("workflow", create_order_graph())
    await cl.Message(
        content="""
        こんにちは！
        当店は幅広いジャンルの書籍を取り扱っております。どのようなものをお探しでしょうか？
        """
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    state = cl.user_session.get("state")
    workflow = cl.user_session.get("workflow")
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    # メッセージを状態に追加
    state["messages"].append(HumanMessage(content=message.content))

    try:
        # ワークフロー実行
        result = await workflow.ainvoke(state, config)

        # 最後のメッセージを取得
        last_message = result["messages"][-1]

        # 商品購入の確認
        if isinstance(last_message, AIMessage) and any(
            call["function"]["name"] == "purchase_items"
            for call in getattr(last_message, "additional_kwargs", {}).get("tool_calls", [])
        ):
            # 商品情報を取得
            item = json.loads(last_message.additional_kwargs["tool_calls"][0]["function"]["arguments"])["item"]
            item_info = f"{item['title']} ({item['price']}円)"
            # 商品画像を表示
            image = get_img()
            await cl.Message(
                content="",
                elements=[image],
            ).send()
            # 購入確認用のアクションボタンを表示
            actions = [
                cl.Action(name="confirm", value="yes", label="購入を確定する"),
                cl.Action(name="cancel", value="no", label="キャンセル"),
            ]
            res = await cl.AskActionMessage(
                content=f"ご注文内容をご確認ください。購入を確定しますか？\n{item_info}", actions=actions
            ).send()
            # 購入の意思を確認できた場合
            if res and res.get("value") == "yes":
                # HACK interruptを挟むと再開時にエラーが発生するため、直接purchase_itemsを呼び出す
                # ref: https://github.com/langchain-ai/langgraph/discussions/544
                tool_call = last_message.additional_kwargs["tool_calls"][0]
                current_messages = result["messages"]
                result = purchase_items.invoke(json.loads(tool_call["function"]["arguments"]))

                # ToolMessageを作成して追加
                tool_message = ToolMessage(
                    content="商品の購入が完了しました",
                    tool_call_id=tool_call["id"],
                    name=tool_call["function"]["name"],
                    additional_kwargs={"arguments": tool_call["function"]["arguments"]},
                )
                current_messages.append(tool_message)

                # 状態を更新
                state["messages"] = current_messages

                # ワークフローを再開
                result = await workflow.ainvoke(state, config)
                if result["messages"]:
                    await cl.Message(content=result["messages"][-1].content).send()
            else:
                await cl.Message(content="ご注文をキャンセルしました。他の商品をお探しいたしましょうか？").send()
        else:
            # 通常の応答を表示
            if result["messages"]:
                await cl.Message(content=result["messages"][-1].content).send()

    except Exception as e:
        logger.error(f"Error: {e}")
        await cl.Message(content=f"申し訳ございません。エラーが発生しました: {str(e)}").send()

    cl.user_session.set("state", state)
