import os
from typing import List

import chromadb
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

HTML_DIR = "./html_files"


from urllib.parse import urljoin, urlparse

VISITED = set()


def is_internal(url):
    return urlparse(url).netloc in ("friscomasjid.org", "www.friscomasjid.org")


def sanitize_filename(url):
    path = urlparse(url).path.strip("/").replace("/", "_")
    return path or "index"


def download_html_assets_recursive(url: str, save_dir: str = HTML_DIR):
    if url in VISITED or not is_internal(url):
        return
    VISITED.add(url)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Save page
        os.makedirs(save_dir, exist_ok=True)
        filename = sanitize_filename(url) + ".html"
        with open(os.path.join(save_dir, filename), "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"[✓] Saved: {url}")

        # Recurse
        for link in soup.find_all("a", href=True):
            next_url = urljoin(url, link["href"])
            download_html_assets_recursive(next_url, save_dir)

    except Exception as e:
        print(f"[✗] Failed at {url}: {e}")


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
    from itertools import chain

    def chunk_text(texts: List[str], chunk_size=250, overlap=50) -> List[str]:
        """
        Combine and chunk text segments into overlapping chunks of words.
        """
        all_text = " ".join(texts)
        words = all_text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = words[i : i + chunk_size]
            if len(chunk) >= 30:
                chunks.append(" ".join(chunk))
        return chunks

    soup = BeautifulSoup(html_content, "html.parser")

    # Find the specific content container
    main_div = soup.find("div", class_="article-content-main")
    if not main_div:
        return []

    # Remove noisy tags within that div
    for tag in main_div.find_all(
        ["script", "style", "nav", "footer", "header", "form", "noscript"]
    ):
        tag.decompose()

    # Extract text from clean tags
    text_elements = main_div.find_all(["h1", "h2", "h3", "h4", "p", "li"])
    segments = [
        el.get_text(strip=True) for el in text_elements if el.get_text(strip=True)
    ]

    # Filter out ones containing "frisco"
    segments = [seg for seg in segments if "frisco" not in seg.lower()]

    # Chunk long combined text
    chunked_segments = chunk_text(segments)

    return list(set(chunked_segments))


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
    print(f"\n🌐 Step 1: Crawling {url}")
    download_html_assets_recursive(url)

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
    sample_file = "./html_files/donate.html"  # Change to any file you know exists
    if os.path.exists(sample_file):
        with open(sample_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        segments = extract_text_from_html(html_content)
        print(f"\n🧩 Extracted {len(segments)} chunk(s):")
        for i, chunk in enumerate(segments, 1):
            print(f"\n--- Chunk {i} ---\n{chunk}\n")
    else:
        print("⚠️ Sample file not found.")
