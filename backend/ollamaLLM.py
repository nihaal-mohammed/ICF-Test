from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import re
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
    context: str = ''
    question: str
    history: list = []

template = """
Here is the conversation history:
{history}

Now, answer the user's question: {question}

Answer:
"""

model = OllamaLLM(model="deepseek-r1")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

@app.post('/ask')
async def ask(request: AskRequest):
    context = request.context
    question = request.question
    history = request.history
    history.append(f"User: {question}")

    try:
        result = chain.invoke({"context": context, "question": question, "history": "\n".join(history)})
        answer = re.split(r'</?think>', result)[-1]

        history.append(f"Bot: {answer}")
        
        return {'answer': answer, 'history': history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=5000, log_level="info")
