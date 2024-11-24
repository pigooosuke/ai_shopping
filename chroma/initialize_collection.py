import csv
import os

import chromadb
from chromadb.api.models import Collection
from chromadb.utils import embedding_functions
from pydantic import BaseModel


class Item(BaseModel):
    id: int
    title: str
    category: str
    price: int
    description: str


class ChromaDBConfig(BaseModel):
    """ChromaDB configuration settings"""

    host: str
    port: int
    collection_name: str
    data_path: str

    @classmethod
    def from_env(cls) -> "ChromaDBConfig":
        """Create configuration from environment variables"""
        return cls(
            host=os.getenv("CHROMA_HOST", "chroma"),
            port=int(os.getenv("CHROMA_PORT", 8000)),
            collection_name=os.getenv("COLLECTION_NAME", "items"),
            data_path=os.getenv("DATA_PATH", "./data/items.csv"),
        )


class ChromaInitializer:
    """ChromaDB initialization handler"""

    def __init__(self, config: ChromaDBConfig):
        self.config = config
        self.encoder = embedding_functions.DefaultEmbeddingFunction()
        self.client = chromadb.HttpClient(host=config.host, port=config.port)

    def _get_or_create_collection(self) -> Collection:
        """Get existing collection or create a new one"""
        try:
            collection = self.client.get_collection(name=self.config.collection_name)
            print(f"Collection '{self.config.collection_name}' already exists.")
        except Exception:
            collection = self.client.create_collection(
                name=self.config.collection_name, metadata={"hnsw:space": "cosine"}
            )
            print(f"Created new collection '{self.config.collection_name}'")
        return collection

    def _prepare_item_data(self, item: Item) -> tuple[str, dict, str]:
        """Prepare item data for ChromaDB"""
        text_to_embed = f"{item.title} {item.category} {item.description}"
        metadata = {
            "title": item.title,
            "price": item.price,
            "category": item.category,
            "description": item.description,
        }
        return text_to_embed, metadata, item.id

    def _load_items_from_csv(self) -> [tuple[str, dict, str]]:
        """Load and process items from CSV file"""
        items_data = []
        with open(self.config.data_path, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                item = Item(**row)
                items_data.append(self._prepare_item_data(item))
        return items_data

    def initialize_collection(self) -> None:
        """Initialize ChromaDB collection with data"""

        collection = self._get_or_create_collection()

        if collection.count() > 0:
            print("Collection already contains data. Skipping initialization.")
            return

        try:
            items_data = self._load_items_from_csv()
            documents, metadatas, ids = zip(*items_data)

            collection.add(documents=list(documents), metadatas=list(metadatas), ids=list(ids))
            print(f"Successfully initialized collection with {len(documents)} items")

        except Exception as e:
            print(f"Error during initialization: {str(e)}")
            raise


def main():
    """Main initialization function"""
    config = ChromaDBConfig.from_env()
    initializer = ChromaInitializer(config)
    initializer.initialize_collection()


if __name__ == "__main__":
    main()
