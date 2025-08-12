import os

import pandas as pd
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

df = pd.read_csv("ICF-events.csv")
embeddings = OllamaEmbeddings(model="mxbai-embed-large")
# print(df.to_string())
db_location = "./chrome_langchain_db"
add_documents = not os.path.exists(db_location)

if add_documents:
    documents = []
    ids = []

    for i, row in df.iterrows():

        document = Document(
            page_content=row["Title"] + " " + row["Room"],
            metadata={"time": row["Time"], "date": row["Date"]},
            id=str(i),
        )
        ids.append(str(i))

        documents.append(document)

vector_store = Chroma(
    collection_name="restaurant_reviews",
    persist_directory=db_location,
    embedding_function=embeddings,
)


if add_documents:
    vector_store.add_documents(documents=documents, ids=ids)

retriever = vector_store.as_retriever(search_kwargs={"k": 5})
#        document = Document(
#           page_content=row["Date"] + " " + row["Time"]+ " " + row["Room"]+ " "+row["Title"],
#          id=str(i)
#     )
