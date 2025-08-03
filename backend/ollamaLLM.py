from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
# Import with error handling for the search function
try:
    from search_chroma import search_chroma
except ImportError as e:
    print(f"Warning: Could not import search_chroma: {e}")
    def search_chroma(query):
        return [["No search functionality available - please fix the import error"]]

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
You are a helpful assistant for the Islamic Center of Frisco. Use the provided context to answer questions accurately and helpfully.

Here is the conversation history:
{history}

Here is the relevant context from the Islamic Center of Frisco:
{context}

User Question: {question}

Instructions:
- Answer based on the provided context when relevant
- Be informative and helpful
- If the context doesn't fully answer the question, provide what information you can
- Keep responses natural and conversational

Answer:
"""

model = OllamaLLM(model="gemma3")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

@app.post('/ask')
async def ask(request: AskRequest):
    question = request.question
    history = request.history + [f"User: {question}"]

    try:
        # 🧠 Use Chroma to fetch relevant context
        relevant_chunks = search_chroma(question)
        
        # 🔗 Process the returned chunks
        # search_chroma returns results["documents"] which is a list of lists
        if relevant_chunks and len(relevant_chunks) > 0:
            # Flatten the nested list structure and join chunks
            all_chunks = []
            for chunk_list in relevant_chunks:
                if isinstance(chunk_list, list):
                    all_chunks.extend(chunk_list)
                else:
                    all_chunks.append(chunk_list)
            
            dynamic_context = "\n\n".join(all_chunks)
        else:
            dynamic_context = "No relevant context found."

        # 🗣️ Send to model
        answer = chain.invoke({
            "context": dynamic_context,
            "question": question,
            "history": "\n".join(history)
        })

        history.append(f"Bot: {answer}")
        
        return {
            'answer': answer, 
            'history': history,
            'context_chunks_found': len(relevant_chunks) if relevant_chunks else 0
        }

    except Exception as e:
        print(f"Error in ask endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/')
async def root():
    return {"message": "Islamic Center of Frisco RAG System is running!"}

@app.get('/health')
async def health():
    return {"status": "healthy", "message": "API is working correctly"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=5000, log_level="info")