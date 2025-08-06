import os
from typing import List

import chromadb
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from bs4.element import Comment


HTML_DIR = "./html_files"


from urllib.parse import urljoin, urlparse

VISITED = set()

the_bad_list = []

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
        
def get_filtered_absolute_links(url, domain):
    try:
        counter = 0
        response = requests.get(url)
        response.raise_for_status()  

        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')

        absolute_links = set()
        excluded_extensions = ('.png', '.jpg', '.jpeg', '.pdf', '.img')
        
        for link in links:
            href = link.get('href')
            if href:
                absolute_link = urljoin(url, href) 
                if (absolute_link.startswith(domain) and 
                    not any(absolute_link.endswith(ext) for ext in excluded_extensions)):
                    print(absolute_link)
                    absolute_links.add(absolute_link)
                    counter+=1
        print(len(absolute_links))
        return absolute_links

    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return {}


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
    
    response = requests.get(html_content)
    html = response.text

    # Step 2: Use BeautifulSoup to parse it
    soup = BeautifulSoup(html, "html.parser")

    # Step 3: Function to filter visible elements
    def tag_visible(element):
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True

    # Step 4: Extract visible text
    texts = soup.find_all(string=True)
    visible_texts = filter(tag_visible, texts)
    visible_strings = [t.strip() for t in visible_texts if t.strip()]
    visible_strings = visible_strings[265:]
    visible_strings = visible_strings[:-23]

    # Chunk long combined text
    chunked_segments = chunk_text(visible_strings)

    for text in visible_strings:
        print(text)

    print(chunked_segments)

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
        #client.delete_collection("frisco_events")

        # ✅ Upload documents, embeddings, and their IDs
        collection.add(documents=documents, embeddings=embeddings, ids=ids)

        print(f"[✓] Uploaded {len(ids)} embeddings to ChromaDB.")

    except Exception as e:
        print(f"[✗] Failed to upload to ChromaDB: {e}")


def html_to_chroma_pipeline(url: str, i: int) -> bool:
    #print(f"\n🌐 Step 1: Crawling {url}")
    #download_html_assets_recursive(url)

    #print("📂 Step 2: Loading HTML files...")
    #html_files = load_html_files_from_directory(HTML_DIR)
    #print(f"  └ Loaded {len(html_files)} HTML file(s)")

    all_text_segments = []
    all_ids = []

    print("📝 Step 3: Extracting text segments from HTML...")
    segments = extract_text_from_html(url)
        #print(f"  └ File {i}: extracted {len(segments)} segments")
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

    segments123 = extract_text_from_html(url)
    if all(""""The Islamic Center of Frisco was established in May 2007. We are located approximately 27 miles north of downtown Dallas. Along with providing daily prayer facilities, ICF also offers various Islamic education services including our successful Quran Academy, Sunday School, and Safwah Seminary educational programs, a vibrant youth group, educational seminars, youth and adult education classes, summer school, nikkah services, and Islamic counseling.""" not in element for element in segments123): 
        return True
    return False

if __name__ == "__main__":
    # Start crawling from homepage instead of just /programs/events
    website_url = "https://friscomasjid.org"
    domain = "https://friscomasjid.org" 
    filtered_links = get_filtered_absolute_links(website_url, domain)
    counter = 0
    bad_links = []
    for i, link in enumerate(filtered_links):
        bad_links.append(link)
        if(html_to_chroma_pipeline(link, i)):
            counter+=1
            bad_links.remove(link)
    print(counter)
    print(bad_links)
    print()
    print()
    print(the_bad_list)
        