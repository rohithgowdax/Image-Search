import asyncio
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService

async def main():
    print("Init embedding service")
    e = EmbeddingService()
    await e.initialize()
    print("Embedding text")
    emb = await e.embed_text('test')
    print("Vector store search")
    v = VectorStoreService()
    res = v.search_similar(emb)
    print("Result:", res)

if __name__ == "__main__":
    asyncio.run(main())
