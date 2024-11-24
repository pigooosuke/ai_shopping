import json
import random

import chainlit as cl
from langchain_core.messages import AIMessage, ToolMessage
from models import State, Item
from tools import purchase_items
from langgraph.graph.state import CompiledStateGraph
from typing import Optional
from langchain_core.runnables import RunnableConfig
from typing import Annotated

from langchain_core.messages.base import BaseMessage
from langgraph.graph.message import add_messages


class ImageHandler:
    @staticmethod
    def get_random_book_image() -> cl.Image:
        """ランダムな本の画像を取得する"""
        img_id = random.randint(1, 4)
        return cl.Image(path=f"./imgs/book_{img_id}.png", name=f"image_{img_id}", display="inline")


class OrderProcessHandler:
    def __init__(
        self,
        state: State,
        workflow: CompiledStateGraph,
        config: RunnableConfig,
        current_messages: Annotated[list[BaseMessage], add_messages],
    ):
        self.state = state
        self.workflow = workflow
        self.config = config
        self.current_messages = current_messages

    async def process_purchase_confirmation(self, message: AIMessage) -> Optional[dict]:
        """購入確認プロセスを処理する"""
        tool_call = message.additional_kwargs["tool_calls"][0]
        item = Item.parse_obj(json.loads(tool_call["function"]["arguments"])["item"])

        # 購入確認
        if await self._confirm_purchase(item):
            return await self._complete_purchase(tool_call)
        else:
            return await self._cancel_purchase(tool_call)

    @staticmethod
    async def _confirm_purchase(item: Item) -> bool:
        """購入の確認を取る"""
        # 画像を表示
        image = ImageHandler.get_random_book_image()
        await cl.Message(content="", elements=[image]).send()
        # 購入意思確認
        res = await cl.AskActionMessage(
            content=f"ご注文内容をご確認ください。購入を確定しますか？\n{item.format_info()}",
            actions=[
                cl.Action(name="confirm", value="yes", label="購入を確定する"),
                cl.Action(name="cancel", value="no", label="キャンセル"),
            ],
        ).send()
        if res is None:
            return False
        return res and res.get("value") == "yes"

    async def _complete_purchase(self, tool_call: dict) -> dict:
        """購入を完了し、結果を返す"""
        # HACK interruptを挟むと再開時にエラーが発生する
        # 直接purchase_itemsを呼び出した後に、tool_call_idに対応する応答を手動追加する
        # ref: https://github.com/langchain-ai/langgraph/discussions/544
        _ = purchase_items.invoke(json.loads(tool_call["function"]["arguments"]))

        tool_message = ToolMessage(
            content="商品の購入が完了しました",
            tool_call_id=tool_call["id"],
            name=tool_call["function"]["name"],
            additional_kwargs={"arguments": tool_call["function"]["arguments"]},
        )
        self.current_messages.append(tool_message)

        self.state["messages"] = self.current_messages
        return await self.workflow.ainvoke(self.state, self.config)

    async def _cancel_purchase(self, tool_call: dict) -> dict:
        """購入をキャンセルし、結果を返す"""
        # HACK interruptを挟むと再開時にエラーが発生する
        # tool_call_idに対応する応答を手動追加する
        # ref: https://github.com/langchain-ai/langgraph/discussions/544

        tool_message = ToolMessage(
            content="商品の購入をキャンセルしました",
            tool_call_id=tool_call["id"],
            name=tool_call["function"]["name"],
        )
        self.current_messages.append(tool_message)

        self.state["messages"] = self.current_messages
        return await self.workflow.ainvoke(self.state, self.config)
