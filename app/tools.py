import json
import os
from logging import getLogger

import chromadb
import payjp
from langchain.schema.runnable.config import RunnableConfig
from langchain_core.tools import tool
from models import ChromaDBConfig, Customer, Item

logger = getLogger(__name__)


@tool
def fetch_customer_info(config: RunnableConfig) -> Customer:
    """ユーザー情報の取得"""
    with open("test_customer.json") as f:
        customer = json.load(f)
    return Customer(id=customer["customer_id"])


@tool
def search_items(query: str, config: RunnableConfig) -> list[Item]:
    """
    ユーザーが求めている商品の検索を行う
    Args:
        query: 検索クエリ
        config: RunnableConfig
    Returns:
        list[Item]: 商品情報のリスト
    """
    chroma_config = ChromaDBConfig.from_env()
    client = chromadb.HttpClient(host=chroma_config.host, port=chroma_config.port)
    collection = client.get_collection(name=chroma_config.collection_name)
    try:
        results = collection.query(
            query_texts=[query],
            n_results=3,
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

    items = []
    for i in range(len(results["ids"][0])):
        metadata = results["metadatas"][0][i]
        items.append(
            Item(
                id=results["ids"][0][i],
                title=metadata["title"],
                category=metadata["category"],
                price=metadata["price"],
                description=metadata["description"],
            )
        )
    return items


@tool
def purchase_items(item: Item, customer: Customer, config: RunnableConfig) -> None:
    """
    商品の購入処理を行う
    Args:
        item: 購入商品
        customer: 購入者情報
        config: RunnableConfig
    """
    payjp.api_key = os.getenv("PAYJP_API_KEY")
    try:
        charge = payjp.Charge.create(
            amount=item.price,
            customer=customer.id,
            currency="jpy",
            metadata={"item_id": item.id, "via": "chatbot"},
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
