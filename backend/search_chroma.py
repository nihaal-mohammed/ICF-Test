import json

import chromadb

from vector_db_pipline import vectorize_text_segments
<<<<<<< HEAD

=======
>>>>>>> c95953ad9ae35ed3f93b3d874895063a62087613

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

        print(results)

        # print(
        #     f"[✓] Search results for query '{query}': {len(results['documents'])} found."
        # )
        return results["documents"]

    except Exception as e:
        print(f"[✗] Failed to upload to ChromaDB: {e}")


print(
    json.dumps(
<<<<<<< HEAD
        search_chroma("funeral"),
=======
        search_chroma(
            ""
            ),
>>>>>>> c95953ad9ae35ed3f93b3d874895063a62087613
        indent=4,
    )
)
