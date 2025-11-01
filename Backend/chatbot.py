# chatbot.py

from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain.memory import ConversationBufferMemory
from paper_check import get_papers, get_relevent_chunks, prepare_paper_for_qa, get_references
import os
import json

# This dictionary will store memory objects, with user_id as the key.
user_memories = {}

def get_user_memory(user_id: str) -> ConversationBufferMemory:
    """Retrieves or creates a memory object for a given user."""
    if user_id not in user_memories:
        user_memories[user_id] = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    return user_memories[user_id]

# Initialize the LLM
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.5, api_key=os.getenv("GROQ_API_KEY"))

# Define tools
@tool
def get_related_papers(action_input: str) -> list:
    """Searches for academic research papers. Input must be a JSON string like '{"query": "topic", "results": 3}'."""
    try:
        params = json.loads(action_input)
        query = params["query"]
        results = params.get("results", 5)
        ans = get_papers(query, results)
        return ans if ans else ["No Papers Found"]
    except Exception as e:
        return f"Error: Invalid JSON input. {e}."

@tool
def retrieve_data(query: str) -> list:
    """Retrieves details from papers already saved in the database. Use for follow-up questions."""
    return get_relevent_chunks(query)

@tool
async def save_paper_for_qa(paper_id: str) -> str:
    """Saves a paper to the database for detailed questioning. Input must be a paper's ArXiv ID."""
    return await prepare_paper_for_qa(paper_id)

@tool
def get_paper_references(paper_id: str) -> list:
    """Lists the academic references for a given paper. Input must be a paper's ArXiv ID."""
    return get_references(paper_id)

tools = [get_related_papers, retrieve_data, save_paper_for_qa, get_paper_references]

# Setup the prompt
prompt = hub.pull("hwchase17/react-chat")
system_prompt_rules = """
You are a helpful research assistant. Your goal is to help users find, save, and understand academic papers.
**YOUR WORKFLOW AND RULES:**
1.  **Finding Papers:** Use `get_related_papers` when asked for papers.
2.  **Saving a Paper:** Use `save_paper_for_qa` when the user expresses interest in a specific paper.
3.  **Answering Questions:** Use `retrieve_data` for questions about a saved paper.
4.  **Listing References:** Use `get_paper_references` for citations.
5.  **Conversational Answers**: For simple chat, answer directly.
"""
prompt.template = system_prompt_rules + "\n\n" + prompt.template

def create_chat_executor(user_id: str) -> AgentExecutor:
    """Creates an AgentExecutor with user-specific memory."""
    user_memory = get_user_memory(user_id)
    
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
        memory=user_memory,
        async_mode=True
    )
    return executor