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

header_and_footer = True
        
def get_filtered_absolute_links(url, domain):
    
    # Collect all the URLs on each page and go through them, adding them to a list to be scraped if they start with friscomasjid.org 
    try:
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
                if (absolute_link.startswith(domain) and not any(absolute_link.endswith(ext) for ext in excluded_extensions)):
                    absolute_links.add(absolute_link)

        return absolute_links
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return {}

def extract_text_from_html(html_content: str) -> List[str]:
    from itertools import chain

    def chunk_text(texts: List[str], link: str, chunk_size=250, overlap=50) -> List[str]:
        """
        Combine and chunk text segments into overlapping chunks of words.
        """
        # Chunks of size <= 280  words, with an overlap of 50 going into the next chunk (for text with length of 300 words, the first chunk will be 250 words and
        # the second shunk will start from the 200th word of the first chunk to be 100 words) 
        all_text = " ".join(texts)
        words = all_text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = words[i : i + chunk_size]
            if len(chunk) >= 30:
                chunks.append(link + " " + " ".join(chunk))
            else:
                if chunks:
                    chunks[-1] += " ".join(chunk)
                else:
                    chunks.append(link + " " + " ".join(chunk))
        return chunks
    
    # Get text from website
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

    #Filter out header and footer text
    visible_strings = visible_strings[265:]
    visible_strings = visible_strings[:-23]

    # Chunk long combined text
    chunked_segments = chunk_text(visible_strings, html_content)

    return list(set(chunked_segments))


def vectorize_text_segments(text_segments: List[str]) -> List[List[float]]:
    """
    Converts a list of text segments into embeddings using Qwen.

    Args:
        text_segments (List[str]): List of textual content to vectorize.

    Returns:
        List[List[float]]: A list of vector embeddings.
    """

    model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
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

def extract_prayer_times_and_contact():
    # Gets text from madinaapps for prayer times and uploads static info about Frisco Masjid
    response = requests.get("https://services.madinaapps.com/kiosk-rest/clients/242/prayerTimes")
    contact_string = """
    About Us The Islamic Center of Frisco was established in May 2007. We are located approximately 27 miles north of downtown Dallas.  Along with providing
    daily prayer facilities, ICF also offers various Islamic education services including our successful Quran Academy, Sunday School, and Safwah Seminary
    educational programs, a vibrant youth group, educational seminars, youth and adult education classes, summer school, nikkah services, and Islamic counseling. 
    Contact Us Address: 11137 Frisco St, Frisco TX 75033 Main Phone: (469) 252-4532 | Clinic Phone: (469) 213-8707 | contact@friscomasjid.org EIN: 20-8679388
    """
    upload_embeddings_to_chroma(vectorize_text_segments(contact_string), contact_string, "doc_-1_-1")
    return [response.text]

def html_to_chroma_pipeline(url: str, i: int):
    all_text_segments = []
    all_ids = []

    print("📝 Step 3: Extracting text segments from link...")

    # Calls method to extract text from wesbite
    if(url != "https://services.madinaapps.com/kiosk-rest/clients/242/prayerTimes"):
        segments = extract_text_from_html(url)
    else:
        segments = extract_prayer_times_and_contact()
    all_text_segments.extend(segments)
    all_ids.extend([f"doc_{i}_{j}" for j in range(len(segments))])

    # If the link has no text , return nothing
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
    # Delete initial ChromaDB collection   
    client = chromadb.PersistentClient(path="chroma")
    collection = client.get_or_create_collection(name="frisco_events")
    client.delete_collection("frisco_events")
    website_url = "https://friscomasjid.org"
    domain = "https://friscomasjid.org" 
    filtered_links = {"https://services.madinaapps.com/kiosk-rest/clients/242/prayerTimes"}
    filtered_links.update(get_filtered_absolute_links(website_url, domain))
    for i, link in enumerate(filtered_links):
        html_to_chroma_pipeline(link, i)

        



