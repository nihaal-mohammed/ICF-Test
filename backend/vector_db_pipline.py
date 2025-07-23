import os
from typing import List

import chromadb
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

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


def load_html_files_from_directory(directory: str) -> list[str]:
    """
    Loads all HTML files from a specified directory.

    Args:
        directory (str): Path to the directory containing HTML files.

    Returns:
        List[str]: A list of HTML strings loaded from the files.
    """
    html_contents = []

    if not os.path.exists(directory):
        print(f"[✗] Directory '{directory}' does not exist.")
        return []

    for filename in os.listdir(directory):
        if filename.endswith(".html") or filename.endswith(".htm"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    html_contents.append(f.read())
            except Exception as e:
                print(f"[✗] Could not read {filename}: {e}")

    print(f"[✓] Loaded {len(html_contents)} HTML file(s) from '{directory}'")
    return html_contents


def extract_text_from_html(html_content: str) -> List[str]:
    """
    Converts an HTML string into plain text, breaking it down into text elements.

    Args:
        html_content (str): Raw HTML string.

    Returns:
        List[str]: A list of extracted plain text segments (e.g., paragraphs, headings).
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract common text-bearing tags
    text_elements = soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "span", "a"])

    # Extract text, strip whitespace, and filter out empty strings
    segments = [
        el.get_text(strip=True) for el in text_elements if el.get_text(strip=True)
    ]

    # Optional: Filter out short or repetitive/junk text (customize as needed)
    filtered_segments = [
        seg
        for seg in segments
        if len(seg) > 30
        and not any(
            kw in seg.lower()
            for kw in [
                "donate",
                "login",
                "home",
                "frisco masjid",
                "contact",
                "prayer times",
            ]
        )
    ]

    # Remove duplicates
    unique_segments = list(set(filtered_segments))

    return unique_segments


def vectorize_text_segments(text_segments: List[str]) -> List[List[float]]:
    """
    Converts a list of text segments into embeddings using OpenAI.

    Args:
        text_segments (List[str]): List of textual content to vectorize.

    Returns:
        List[List[float]]: A list of vector embeddings.
    """
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(text_segments, convert_to_numpy=True).tolist()
    return embeddings


def upload_embeddings_to_chroma(
    embeddings: List[List[float]], documents: List[str], ids: List[str]
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

        # ✅ Upload documents, embeddings, and their IDs
        collection.add(documents=documents, embeddings=embeddings, ids=ids)

        print(f"[✓] Uploaded {len(ids)} embeddings to ChromaDB.")

    except Exception as e:
        print(f"[✗] Failed to upload to ChromaDB: {e}")


def html_to_chroma_pipeline(url: str):
    print(f"\n🌐 Step 1: Downloading HTML from {url}")
    download_html_assets(url)

    print("📂 Step 2: Loading HTML files...")
    html_files = load_html_files_from_directory(HTML_DIR)
    print(f"  └ Loaded {len(html_files)} HTML file(s)")

    all_text_segments = []
    all_ids = []

    print("📝 Step 3: Extracting text segments from HTML...")
    for i, html_content in enumerate(html_files):
        segments = extract_text_from_html(html_content)
        print(f"  └ File {i}: extracted {len(segments)} segments")

        all_text_segments.extend(segments)
        all_ids.extend([f"doc_{i}_{j}" for j in range(len(segments))])

    if not all_text_segments:
        print("[✗] No text segments extracted. Exiting.")
        return

    print(f"\n🔍 Total text segments to embed: {len(all_text_segments)}")

    print("🧠 Step 4: Vectorizing text segments ...")
    embeddings = vectorize_text_segments(all_text_segments)
    print(f"  └ Got {len(embeddings)} embeddings")

    if not embeddings:
        print("[✗] Embedding generation failed or returned nothing.")
        return

    print("📤 Step 5: Uploading to ChromaDB...")
    upload_embeddings_to_chroma(embeddings, all_text_segments, all_ids)

    print("✅ Pipeline complete!")


if __name__ == "__main__":
    # Example usage
    target_url = "https://friscomasjid.org/programs/events"
    html_to_chroma_pipeline(target_url)
