import json

import chromadb
from vector_db_pipline import vectorize_text_segments


def search_chroma(
    query: str,
):
    """
    Uploads vector embeddings along with their original documents into a persistent Chroma database.

    Args:
        embeddings (List[List[float]]): List of embedding vectors.
        documents (List[str]): List of original text documents.
        ids (List[str]): Unique identifiers for each document.

    Returns:
        None
    """
    try:
        # ✅ Initialize persistent ChromaDB client
        client = chromadb.PersistentClient(path="chroma")
        # ✅ Create or connect to a collection
        collection = client.get_or_create_collection(name="frisco_events")

        # embed query
        query_embeddings = vectorize_text_segments([query])[0]
        # ✅ Upload documents, embeddings, and their IDs
        results = collection.query(query_embeddings=query_embeddings, n_results=5)

        # Step 3: Write to a text file
        # with open('put your own file path here', 'w') as file:
        #     file.write(json.dumps(results))

        # print(
        #     f"[✓] Search results for query '{query}': {len(results['documents'])} found."
        # )
        return results["documents"]

    except Exception as e:
        print(f"[✗] Failed to upload to ChromaDB: {e}")
