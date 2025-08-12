from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from vector import retriever

model = OllamaLLM(model="gemma3")

template = """
You are an assistant for the Islamic Center of Frisco.

Answer concisely:
- Max 2–3 short sentences, or up to 5 bullet points.
- No filler, no restating the question, no disclaimers.
- If the user asks for today's prayer times, output ONLY:
  Fajr: <time>
  Dhuhr: <time>
  Asr: <time>
  Maghrib: <time>
  Isha: <time>

Context:
{context}

Question:
{question}
"""
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

while True:
    print("\n\n-------------------------------")
    question = input("Ask your question (q to quit): ")
    print("\n\n")
    if question == "q":
        break

    reviews = retriever.invoke(question)
    result = chain.invoke({"reviews": reviews, "question": question})
    print(result)
