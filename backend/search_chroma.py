import json

import chromadb

from vector_db_pipline import vectorize_text_segments

import re

import nltk

from nltk.corpus import stopwords

nltk.download('stopwords')

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

        # Embed Query and perform vector search
        query_embeddings = vectorize_text_segments([query])[0]
        results = collection.query(query_embeddings=query_embeddings, n_results=5)  # Run the query once for top 5 results

        # Hybrid Search - Keyword and Vector Search
        # Could be improved to first try and include all n keywords , then n-1 keywords, then n-2 keywords, etc.  
        # Phrasing of questions can affect answers sometimes "What is the daily imam schedule for ICF?" vs "daily imam schedule" - and some questions are inconsistent
        # Create stop words to filter out
        stop_words = set(stopwords.words('english'))
        stop_words.update(["icf", "frisco", "masjid", "islamic", "center"])

        # Create new sets for capitalized, uppercase, and lowercase versions
        capitalized_stop_words = {word.capitalize() for word in stop_words}
        uppercase_stop_words = {word.upper() for word in stop_words}
        lowercase_stop_words = {word.lower() for word in stop_words}

        # Update stop_words after creating the new sets
        new_stop_words = capitalized_stop_words | uppercase_stop_words | lowercase_stop_words
        stop_words.update(new_stop_words)
        # Remove punctuation and split the query into words
        words = re.findall(r'\w+', query)
        # Filter out stop words
        keywords = [word for word in words if word not in stop_words]
        keywords_set = set(keywords)
        capitalized_keywords = {word.capitalize() for word in keywords_set}
        uppercase_keywords = {word.upper() for word in keywords_set}
        lowercase_keywords = {word.lower() for word in keywords_set}
        new_key_words = capitalized_keywords | uppercase_keywords | lowercase_keywords
        keywords_set.update(new_key_words)

        # Create filter to contain keywords 
        if(len(keywords_set) == 0):
            return results["documents"]
        if(len(keywords_set) > 1):
            where_conditions = [{"$contains": string} for string in keywords_set]
        else:
            where_conditions = {'$contains': next(iter(keywords_set))}

        # Run the vector search of the original query with the keyword filters
        if(len(where_conditions) >= 2):
            filtered_results = collection.query(
                query_embeddings=query_embeddings,
                where_document={
                    "$or": where_conditions
                }
            )
        else:     
            filtered_results = collection.query(
                query_embeddings=query_embeddings,
                where_document=where_conditions#,
            )

        # Retrieve 3 unique text chunks from the filtered vector search
        unique_keyword_results = []
        for i in range(0, len(filtered_results["documents"])):
            if not any(filtered_results["documents"][i] in doc for doc in results["documents"]):
                unique_keyword_results.append(filtered_results["documents"][i])
                if(len(unique_keyword_results) == 3):
                    break

        return results["documents"] + unique_keyword_results

    except Exception as e:
        print(f"[✗] Failed to upload to ChromaDB: {e}")

