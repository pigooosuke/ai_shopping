import os

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import ChatOpenAI
from models import State
from tools import purchase_items, search_items


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls and (
                not result.content or isinstance(result.content, list) and not result.content[0].get("text")
            ):
                messages = state["messages"] + [HumanMessage(content="Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


def create_assistant():
    """アシスタントの作成"""
    api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, temperature=0)

    # プロンプトの設定
    assistant_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "あなたは書籍を専門としたECサイトのショッピングアシスタントです。"
                "与えられたツールを利用し、ユーザーに対して書籍の検索と購入のサポートを行なってください。"
                "登録されている商品名をユーザーが購入したい場合は、購入処理に進んでください"
                "\n\nCurrent customer:\n<Customer>\n{customer_info}\n</Customer>",
            ),
            ("placeholder", "{messages}"),
        ]
    )
    # アシスタントがツールを実行できるように設定
    assistant_runnable = assistant_prompt | llm.bind_tools([search_items, purchase_items], parallel_tool_calls=False)

    return Assistant(assistant_runnable)
