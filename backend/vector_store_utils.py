import chromadb
from vector_db_pipline import vectorize_text_segments  # adjust if needed

def embed_text_from_string(text: str, doc_id="icf_001", collection_name="frisco_events"):
    try:
        # Get embedding
        embeddings = vectorize_text_segments([text])

        # Set up ChromaDB
        client = chromadb.PersistentClient(path="chroma")
        collection = client.get_or_create_collection(name=collection_name)

        # Add document
        collection.add(
            documents=[text],
            embeddings=embeddings,
            ids=[doc_id]
        )

        print(f"[✓] Document '{doc_id}' successfully added to collection '{collection_name}'.")

    except Exception as e:
        print(f"[✗] Failed to embed document: {e}")
