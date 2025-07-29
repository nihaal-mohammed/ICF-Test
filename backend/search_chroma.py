import json

import chromadb

from BackEnd.vector_db_pipline import vectorize_text_segments


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
        results = collection.query(query_embeddings=query_embeddings, n_results=10)

        # print(
        #     f"[✓] Search results for query '{query}': {len(results['documents'])} found."
        # )
        return results["documents"]

    except Exception as e:
        print(f"[✗] Failed to upload to ChromaDB: {e}")


print(
    json.dumps(
        search_chroma(
            "Welcome to the Islamic Center of Frisco, a rapidly growing community masjid established in 2007 with a goal to provide a warm and welcoming environment for all to gather, pray, and learn. Our facility offers a place to play and is a hub for various educational programs as well as outreach, counseling, and community assistance programs to serve those in need. Our journey at the Islamic Center of Frisco started with humble beginnings, but with the help of Allah (SWT) and the generosity of our community, we have seen rapid growth and success. We are located approximately 27 miles north of downtown Dallas and have been fortunate enough to call our current facility on Frisco Street our home for the past 6 years. The muslim population in Frisco has grown significantly over the past 6 years, and we are proud to be a part of the growing community. We are dedicated to providing a welcoming and inclusive space for all to worship, learn, and grow. Our current facility includes a place to play, educational programs, and community assistance programs to serve those in need. ICF is proud to offer various programs and services to cater to our diverse population. Our Sunday School program, run solely by a team of 40+ volunteers, currently has over 450 students with over 100 students on the waitlist. The Safwah Youth Seminary program has over 200 kids enrolled and focuses on fiqh, seerah, and aqeedah. The Quran Academy offers full-time and part-time hifdh programs, along with nazirah and qaidah programs. Our newly launched Uswah Adult Seminary program offers continuing education opportunities for adults in Islamic Studies with a comprehensive 2-year program. Additionally, we also offer a free health clinic on a weekly basis to provide medical care and physician consultation to those who are uninsured, completely free of charge. We are constantly striving to better serve our community and provide more opportunities for worship, education, and growth. We are excited for what the future holds for the Islamic Center of Frisco, and we look forward to continuing to serve and grow the muslim community in Frisco. Join us in our mission to serve and grow the community at the Islamic Center of Frisco. Together, we can create a welcoming and inclusive space for all to worship, learn, and grow."
        ),
        indent=4,
    )
)
