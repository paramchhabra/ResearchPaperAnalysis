import arxiv
import fitz  # PyMuPDF
from typing import List
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_groq import ChatGroq
import asyncio
import time
import os
from db import vector_db_pdf # Assuming you have a db.py for this
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

GROQ_RETR_API = os.getenv("GROQ_RETR_API")
VECTOR_DIR = "stored_vector_db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def get_vector_store():
    return Chroma(persist_directory=VECTOR_DIR, embedding_function=HuggingFaceEmbeddings(model_name=MODEL_NAME))

def get_references(paper_id: str) -> list:
    """Synchronous wrapper for fetching references."""
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{paper_id}"
    params = {"fields": "references.externalIds,references.title"}
    try:
        res = requests.get(url, params=params)
        res.raise_for_status() # Raise an exception for bad status codes
        data = res.json()
        if "references" not in data or not data["references"]:
            return ["No references with ArXiv IDs found."]
        
        sol = data["references"]
        ids = []
        for i in sol:
            # Ensure the reference has both a title and an ArXiv ID
            if i and i.get("externalIds") and "ArXiv" in i["externalIds"] and i.get("title"):
                ids.append({"title": i["title"], "id": i["externalIds"]["ArXiv"]})
        return ids if ids else ["No references with ArXiv IDs found."]
    except requests.exceptions.RequestException as e:
        return [f"Could not fetch references: {e}"]
    except Exception as e:
        return [f"An error occurred while processing references: {e}"]


async def place_in_db(doc: dict) -> bool:
    doc["references"] = get_references(doc["paper_id"]) # Changed to call the sync function
    await vector_db_pdf.insert_one(doc)
    return True

def get_papers(query: str, results: int) -> list:
    search = arxiv.Search(query=query, max_results=results)
    # Returning a dictionary for more structured data
    ans = [{"id": i.get_short_id()[:-2], "title": i.title, "summary": i.summary} for i in search.results()]
    return ans
# print(get_papers("engine",2))
async def download_pdf(pap_id: str) -> tuple:
    search = arxiv.Search(id_list=[pap_id], max_results=1)
    try:
        result = next(search.results())
    except StopIteration:
        return None, {"error": f"Paper with ID {pap_id} not found on ArXiv."}

    query = await vector_db_pdf.find_one({"paper_id": pap_id})
    pdf_path = f"{pap_id}_{result.title.replace(' ', '_')}.pdf"
    res_dict = {
        "paper_id": pap_id,
        "paper_title": result.title,
        "paper_summary": result.summary,
    }
    if query is None:
        await place_in_db(res_dict)
        result.download_pdf(filename=pdf_path)
        return pdf_path, res_dict
    else:
        return None, query

vector_store = get_vector_store()

async def save_embeddings(pap_id: str):
    file_name, paper_details = await download_pdf(pap_id=pap_id)

    if paper_details.get("error"):
        print(paper_details["error"])
        return paper_details["error"]

    if file_name:
        with fitz.open(file_name) as f:
            full_text = ""
            for page in f:
                full_text += page.get_text()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(full_text)
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "paper_id": paper_details["paper_id"],
                    "title": paper_details["paper_title"],
                    "summary": paper_details["paper_summary"]
                }
            )
            for chunk in chunks
        ]

        await vector_store.aadd_documents(documents=documents)
        # vector_store.persist()
        os.remove(file_name)
        msg = f"Paper '{paper_details['paper_title']}' has been successfully saved to the database for Q&A."
        print(msg)
        return msg
    else:
        msg = f"Paper '{paper_details['paper_title']}' already exists in the database."
        print(msg)
        return msg

# --- NEW FUNCTION TO BE CALLED BY THE AGENT TOOL ---
async def prepare_paper_for_qa(pap_id: str) -> str:
    """Synchronous wrapper to run the async save_embeddings function."""
    # return asyncio.run(save_embeddings(pap_id))
    return await save_embeddings(pap_id)
# ----------------------------------------------------

# prepare_paper_for_qa("2101.10848")

metadata_field_info = [
    AttributeInfo(name="paper_id", description="The unique arXiv paper ID", type="string"),
    AttributeInfo(name="title", description="The title of the research paper", type="string"),
    AttributeInfo(name="summary", description="A one-line summary of the research paper", type="string"),
]
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_RETR_API)
summary_data = "Contains Arxiv Research papers with paper Id, Title, Summary"
retriever = SelfQueryRetriever.from_llm(llm, vector_store, summary_data, metadata_field_info)

def get_relevent_chunks(query: str) -> list:
    return retriever.invoke(query)