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

context = """
Sunday School Times:
Students in kindergarten to third grade are in the first shift, which is from 9:00 AM to 11:00 AM.

Students in fourth to eighth grade are in the second shift, which is from 11:45 AM to 2:15 PM.

Quran Academy Times:
QAIDAH (1 Hour, 4 Days / Week)
Monday-Thursday, 4:00, 5:00, or 6:00 PM

NAZIRAH (1 Hour, 4 Days / Week)
Monday-Thursday, 4:00, 5:00, or 6:00 PM
OR Saturday, 12:00 - 2:00 PM or 2:00 - 4:00 PM

PART-TIME HIFDH (2 Hours, 4 Days / Week)
Monday-Thursday, 5:00 - 7:00 PM

FULL-TIME HIFDH (6 Hours, 5 Days / Week)
Monday-Friday, 8:00 AM - 2:00 PM

Safwah Seminary:
SCHEDULE
Safwah 101
Tuesdays - 6:00pm - 6:45pm
Saturdays - 11:00am - 11:45pm

Safwah 102
Thursdays - 6:00pm - 6:45pm
Saturdays - 12:00pm - 12:45pm

Safwah 201
Tuesdays - 7:00pm - 7:45pm
Saturdays - 1:00pm - 1:45pm

Safwah 202
Thursdays - 7:00pm - 7:45pm
Saturdays - 2:15pm - 3:00pm
"""



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
