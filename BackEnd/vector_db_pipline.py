import os
from typing import List
import requests
# from bs4 import BeautifulSoup
# import openai
# import chromadb
# from chromadb.config import Settings

HTML_DIR = "./html_files"

def download_html_assets(url: str, save_dir: str = HTML_DIR):
    """
    Downloads all HTML assets from a given URL and saves them in the specified directory.

    Args:
        url (str): The target webpage to download.
        save_dir (str): Directory where the HTML files should be stored.

    Returns:
        None
    """
    # Make sure the directory exists
    os.makedirs(save_dir, exist_ok=True)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise error for bad HTTP status codes

        # Create a filename-safe version of the URL
        filename = "index.html"
        filepath = os.path.join(save_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"[✓] HTML downloaded and saved to {filepath}")

    except requests.exceptions.RequestException as e:
        print(f"[✗] Failed to download HTML from {url}: {e}")


def load_html_files_from_directory(directory: str) -> List[str]:
    """
    Loads all HTML files from a specified directory.

    Args:
        directory (str): Path to the directory containing HTML files.

    Returns:
        List[str]: A list of HTML strings loaded from the files.
    """
    # TODO: List files in the directory
    # TODO: Filter for .html or .htm files
    # TODO: Read the contents of each file and append to a list of strings
    pass


def extract_text_from_html(html_content: str) -> List[str]:
    """
    Converts an HTML string into plain text, breaking it down into text elements.

    Args:
        html_content (str): Raw HTML string.

    Returns:
        List[str]: A list of extracted plain text segments (e.g., paragraphs, headings).
    """
    # TODO: Use `BeautifulSoup` to parse the HTML content
    # TODO: Extract text elements (e.g., <p>, <h1>, <li>, etc.)
    # TODO: Clean/Categorize text as needed and return as a list of strings
    pass


def vectorize_text_segments(text_segments: List[str]) -> List[List[float]]:
    """
    Converts a list of text segments into embeddings using OpenAI.

    Args:
        text_segments (List[str]): List of textual content to vectorize.

    Returns:
        List[List[float]]: A list of vector embeddings.
    """
    # TODO: Set OpenAI API key
    # TODO: Use `openai.Embedding.create` with a model like 'text-embedding-3-small' or 'text-embedding-ada-002'
    # TODO: Return list of embeddings corresponding to input text
    pass


def upload_embeddings_to_chroma(embeddings: List[List[float]], documents: List[str], ids: List[str]):
    """
    Uploads vector embeddings along with their original documents into a persistent Chroma database.

    Args:
        embeddings (List[List[float]]): List of embedding vectors.
        documents (List[str]): List of original text documents.
        ids (List[str]): Unique identifiers for each document.

    Returns:
        None
    """
    # TODO: Initialize persistent Chroma client using `chromadb.Client(Settings(...))`
    # TODO: Create or connect to a collection
    # TODO: Use .add(documents=..., embeddings=..., ids=...) to upload data
    pass


def html_to_chroma_pipeline(url: str):
    """
    Full pipeline: downloads from URL, extracts text, vectorizes it, and uploads to Chroma.

    Args:
        url (str): The source URL to fetch and process.

    Returns:
        None
    """
    # Step 1: Download HTML and save to local directory
    download_html_assets(url)

    # # Step 2: Load HTML files from directory
    # html_files = load_html_files_from_directory(HTML_DIR)

    # all_text_segments = []
    # all_ids = []

    # # Step 3: Extract text from each HTML file
    # for i, html_content in enumerate(html_files):
    #     # Extract meaningful text segments
    #     segments = extract_text_from_html(html_content)
    #     all_text_segments.extend(segments)
    #     # Generate unique IDs (e.g., "doc_0_0", "doc_0_1", etc.)
    #     all_ids.extend([f"doc_{i}_{j}" for j in range(len(segments))])

    # # Step 4: Vectorize the extracted text
    # embeddings = vectorize_text_segments(all_text_segments)

    # # Step 5: Upload vectors + metadata to Chroma DB
    # upload_embeddings_to_chroma(embeddings, all_text_segments, all_ids)

# Optional main section
if __name__ == "__main__":
    # Example usage
    target_url = "https://friscomasjid.org/programs/events"
    html_to_chroma_pipeline(target_url)
