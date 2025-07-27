from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

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

context = """Due to our extensive community growth over the past few years, Sunday School has adopted a two-shift schedule to accommodate additional students while maintaining a productive environment.

Students in kindergarten to third grade are in the first shift, which is from 9:00 AM to 11:00 AM.

Students in fourth to eighth grade are in the second shift, which is from 11:45 AM to 2:15 PM."""

template = """
Here is the conversation history:
{history}

Here is the context:
{context}

Now, answer the user's question: {question}

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
        answer = chain.invoke({
            "context": context,
            "question": question,
            "history": "\n".join(history)
        })
        history.append(f"Bot: {answer}")
        return {'answer': answer, 'history': history}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=5000, log_level="info")
