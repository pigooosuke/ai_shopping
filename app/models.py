import os
from typing import Annotated

from langchain_core.messages.base import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from typing_extensions import TypedDict


class Customer(BaseModel):
    id: str
    name: str = "Alice"


class Item(BaseModel):
    id: int
    title: str
    category: str
    price: int
    description: str


class ItemMetadata(BaseModel):
    id: int
    title: str
    price: int
    category: str


class State(TypedDict):

    messages: Annotated[list[BaseMessage], add_messages]
    customer_info: Customer


class ChromaDBConfig(BaseModel):
    """ChromaDB configuration settings"""

    host: str
    port: int
    collection_name: str

    @classmethod
    def from_env(cls) -> "ChromaDBConfig":
        """Create configuration from environment variables"""
        return cls(
            host=os.getenv("CHROMA_HOST", "chroma"),
            port=int(os.getenv("CHROMA_PORT", 8000)),
            collection_name=os.getenv("COLLECTION_NAME", "items"),
        )
