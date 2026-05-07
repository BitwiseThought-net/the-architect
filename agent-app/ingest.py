from crewai import Crew, Agent
from knowledge_manager import get_all_knowledge_sources
import os

def start_ingestion():
    sources = get_all_knowledge_sources()
    if not sources:
        print("⚠️ No compatible files found in /knowledge")
        return

    # Dummy crew to trigger the local ChromaDB ingestion
    crew = Crew(
        agents=[Agent(role="Librarian", goal="Index", backstory="Indexer", llm=f"openai/ollama/{os.getenv('MODEL_NAME')}")],
        tasks=[],
        knowledge_sources=sources,
        embedder={
            "provider": "ollama",
            "config": {
                "model": "nomic-embed-text",
                "base_url": "http://ollama:11434"
            }
        }
    )

    print(f"🚀 Ingesting {len(sources)} types of documentation into ChromaDB...")
    # This persists data to the volume mapped to your agent-chromadb service
    crew.train(n_iterations=1, inputs={})
    print("✅ Local knowledge base successfully updated.")

if __name__ == "__main__":
    start_ingestion()
