from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
import json
import chromadb
import os
import sys
from typing import List

# Add current directory to Python path to help with imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import your search function with better error handling
search_chroma_function = None

try:
    from search_chroma import search_chroma
    search_chroma_function = search_chroma
    print("✅ Successfully imported search_chroma from search_chroma.py")
except ImportError as e:
    print(f"❌ Could not import from search_chroma.py: {e}")
    
    # Try to create the search function directly here
    try:
        from Backend.vector_db_pipline import vectorize_text_segments
        
        def search_chroma(query: str):
            """
            Search ChromaDB for relevant chunks based on the query.
            Returns results["documents"] which is a list of lists.
            """
            try:
                # Initialize persistent ChromaDB client
                client = chromadb.PersistentClient(path="chroma")
                
                # Create or connect to a collection
                collection = client.get_or_create_collection(name="frisco_events")
                
                # Check if we have documents
                doc_count = collection.count()
                if doc_count == 0:
                    print("⚠️ No documents found in ChromaDB collection 'frisco_events'")
                    return [["No documents found in database. Please run your data pipeline first."]]
                
                # Embed query
                query_embeddings = vectorize_text_segments([query])[0]
                
                # Search for similar documents
                results = collection.query(query_embeddings=query_embeddings, n_results=10)
                
                print(f"[✓] Search results for query '{query[:50]}...': {len(results['documents'][0]) if results['documents'] else 0} found.")
                
                return results["documents"]
                
            except Exception as e:
                print(f"[✗] Failed to search ChromaDB: {e}")
                return [["Error searching database. Please check your setup."]]
        
        search_chroma_function = search_chroma
        print("✅ Created search_chroma function directly with Backend.vector_db_pipline import")
        
    except ImportError as e2:
        print(f"❌ Could not import Backend.vector_db_pipline: {e2}")
        print("💡 Please ensure your Backend/vector_db_pipline.py file exists and is importable")
        
        def search_chroma(query):
            return [["Search functionality not available - please fix import errors"]]
        
        search_chroma_function = search_chroma

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    question: str
    history: list = []

template = """
You are a helpful assistant for the Islamic Center of Frisco (ICF). Use the provided context to answer questions accurately and helpfully.

Here is the conversation history:
{history}

Here is the relevant context from the Islamic Center of Frisco:
{context}

User Question: {question}

Instructions:
- Answer based ONLY on the provided context when available
- If the context contains relevant information, use it to answer the question
- If the context doesn't contain enough information, clearly state that you don't have that information in your database
- Be informative and helpful, but don't make up information not found in the context
- Keep responses natural and conversational
- If no relevant context is found, say "I don't have information about that in my current database"

Answer:
"""

# Initialize the model with error handling
model = None
try:
    model = OllamaLLM(model="gemma3")
    print("✅ Successfully initialized Gemma3 model")
except Exception as e:
    print(f"❌ Error initializing Gemma3: {e}")
    try:
        model = OllamaLLM(model="llama2")
        print("✅ Successfully initialized Llama2 model as fallback")
    except Exception as e2:
        print(f"❌ Error initializing Llama2: {e2}")
        print("💡 Please ensure Ollama is running: ollama serve")
        print("💡 And pull a model: ollama pull gemma3")

if model:
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
else:
    chain = None

@app.post('/ask')
async def ask(request: AskRequest):
    if not chain:
        raise HTTPException(status_code=500, detail="Model not initialized. Please check Ollama setup.")
    
    question = request.question
    history = request.history.copy()  # Don't modify original
    
    # Add current question to history
    current_conversation = history + [f"User: {question}"]

    print("hello")

    try:
        # 🧠 Use Chroma to fetch relevant context
        relevant_chunks = search_chroma(question)
        print("hello2")
        print(relevant_chunks)

        # 🔗 Process the returned chunks
        # search_chroma returns results["documents"] which is a list of lists
        dynamic_context = ""
        chunks_found = 0
        
        if relevant_chunks and len(relevant_chunks) > 0:
            # Flatten the nested list structure and join chunks
            all_chunks = []
            for chunk_list in relevant_chunks:
                if isinstance(chunk_list, list):
                    # Filter out empty strings and error messages
                    valid_chunks = [chunk for chunk in chunk_list if chunk.strip() and not chunk.startswith("No search functionality") and not chunk.startswith("Error searching") and not chunk.startswith("No documents found")]
                    all_chunks.extend(valid_chunks)
                else:
                    if chunk_list.strip() and not chunk_list.startswith("No search functionality"):
                        all_chunks.append(chunk_list)
            
            if all_chunks:
                # Limit to top 5 chunks to avoid overwhelming the model
                top_chunks = all_chunks[:5]
                dynamic_context = "\n\n".join([f"Context {i+1}: {chunk}" for i, chunk in enumerate(top_chunks)])
                chunks_found = len(top_chunks)
                print(f"📚 Using {chunks_found} valid context chunks")
                print(f"📄 First chunk preview: {top_chunks[0][:100]}...")
            else:
                dynamic_context = "No relevant context found in the database."
                print("⚠️ No valid chunks found after filtering")
        else:
            dynamic_context = "No relevant context found in the database."
            print("⚠️ No chunks returned from search")

        # Format conversation history (keep it shorter)
        history_text = "\n".join(current_conversation[-6:])  # Keep last 6 exchanges
        
        # Generate response using the chain
        print("🤖 Generating response with context...")
        answer = chain.invoke({
            "context": dynamic_context,
            "question": question,
            "history": history_text
        })

        # Update history with the new exchange
        updated_history = current_conversation + [f"Bot: {answer}"]
        
        # Keep history manageable (last 20 entries)
        if len(updated_history) > 20:
            updated_history = updated_history[-20:]
        
        return {
            'answer': answer.strip(),
            'history': updated_history,
            'context_chunks_found': chunks_found
        }

    except Exception as e:
        print(f"❌ Error in ask endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get('/')
async def root():
    return {"message": "Islamic Center of Frisco RAG System is running!", "status": "online"}

@app.get('/health')
async def health():
    try:
        # Test ChromaDB
        client = chromadb.PersistentClient(path="chroma")
        collection = client.get_or_create_collection(name="frisco_events")
        doc_count = collection.count()
        
        # Test search function
        test_results = search_chroma_function("test query")
        search_working = len(test_results) > 0 if test_results else False
        
        return {
            "status": "healthy", 
            "message": "API is working correctly",
            "chroma_documents": doc_count,
            "model_status": "working" if chain else "not initialized",
            "search_function": "working" if search_working else "not working",
            "chroma_path": os.path.abspath("chroma")
        }
    except Exception as e:
        return {
            "status": "partial", 
            "message": f"API running but some components have issues: {str(e)}"
        }

@app.get('/test-search')
async def test_search():
    """Test the search functionality directly"""
    try:
        test_query = "Islamic Center programs"
        results = search_chroma_function(test_query)
        
        return {
            "query": test_query,
            "results_type": str(type(results)),
            "results_length": len(results) if results else 0,
            "first_result_preview": str(results[0])[:200] + "..." if results and len(results) > 0 else "No results",
            "raw_results": results
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == '__main__':
    print("🚀 Starting Islamic Center of Frisco RAG Server...")
    print("📋 Setup Status:")
    print(f"   ✓ FastAPI server")
    print(f"   {'✓' if model else '❌'} Ollama model: {'initialized' if model else 'NOT initialized'}")
    print(f"   {'✓' if search_chroma_function else '❌'} Search function: {'available' if search_chroma_function else 'NOT available'}")
    print(f"   📂 ChromaDB path: {os.path.abspath('chroma')}")
    print(f"   🌐 Server URL: http://127.0.0.1:5000")
    print(f"   🔍 Health check: http://127.0.0.1:5000/health")
    print(f"   🧪 Test search: http://127.0.0.1:5000/test-search")
    print(f"   📁 Current directory: {os.getcwd()}")
    print("\n💡 Before testing, ensure:")
    print("   1. Ollama is running: ollama serve")
    print("   2. Model is available: ollama pull gemma3")
    print("   3. ChromaDB has data: check with /health endpoint")
    print("   4. Your search_chroma.py or Backend/vector_db_pipline.py files are accessible")
    print("\n" + "="*60)
    
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=5000, log_level="info")