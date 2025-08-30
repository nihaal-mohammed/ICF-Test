import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from openai import OpenAI
# Import with error handling for the search function
try:
    from search_chroma import search_chroma
except ImportError as e:
    print(f"Warning: Could not import search_chroma: {e}")
    def search_chroma(query):
        return [["No search functionality available - please fix the import error"]]

app = FastAPI()

#Allow requests frmo anywhere - I believe this is needed to run the code locally but would not be good for making this public
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

#System prompt and setting up Github 4.1-mini model
token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.github.ai/inference"
#model_name = "openai/gpt-4o-mini"
model_name = "openai/gpt-4.1-mini"
system_prompt = """
Here is the system prompt:
You are a helpful assistant for the Islamic Center of Frisco. Use the provided context to answer questions accurately and helpfully.
Instructions:
Use the provided context to answer any questions the user has. Look at all the available context and determine the BEST parts of context to use. 
The answer to the user's question should be found in the context, so LOOK CAREFULLY and ANALYZE the context.  The answer can be in the beginning, middle, or 
end of the context, so focus on ALL parts and give the best answer. 
The answer can even be found in one sentence out of the paragraphs of context, so EXAMINE ALL PARTS OF THE CONTEXT CAREFULLY. 
Keep your responses natural and conversational. You are an AI designed to provide accurate and reliable information. Your primary goal is to assist users 
by answering their questions based on verified data and established knowledge. UNDER NO CIRCUMSTANCES should you make up information or 
provide speculative answers. If you do not have sufficient information to answer a question accurately, clearly communicate that to the user. 
Always prioritize HONESTY and TRANSPARENCY in your responses.
"""

@app.post('/ask')
async def ask(request: AskRequest):
    question = request.question
    # Maybe make context a queue of most recent responses to avoid infinitely long context
    history = "Here is the history:" + '\n'.join(request.history + [f"User: {question}"])

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
            
            dynamic_context = "Here is the context:" + "\n\n".join(all_chunks)
        else:
            dynamic_context = "Here is the context: No relevant context found."

        #Create connection to OpenAI with API key and give it all the relevant info
        client = OpenAI(
            base_url=endpoint,
            api_key=token,
        )
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "system",
                    "content": dynamic_context
                },
                {
                    "role": "system",
                    "content": history
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            model=model_name
        )
        answer = response.choices[0].message.content
        history = history.split('\n')
        history.append(f"Bot: {answer}")        
        return {
            'answer': answer, 
            'history': history,
            'context_chunks_found': len(relevant_chunks) if relevant_chunks else 0
        }

    # Add timeout of ~30 seconds
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