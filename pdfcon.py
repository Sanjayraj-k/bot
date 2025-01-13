import streamlit as st
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain import hub
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
import os
from PyPDF2 import PdfReader

# Initialize the language model and embeddings
llm = ChatGroq(model="llama3-8b-8192")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
vector_store = Chroma(embedding_function=embeddings)

# Function to load and process documents
def load_texts(text_folder: str):
    documents = []
    for filename in os.listdir(text_folder):
        file_path = os.path.join(text_folder, filename)
        if filename.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()
                documents.append(Document(page_content=text, metadata={"source": filename}))
        elif filename.endswith(".pdf"):
            pdf_reader = PdfReader(file_path)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            documents.append(Document(page_content=text, metadata={"source": filename}))
    if not documents:
        raise ValueError(f"No documents found in the folder: {text_folder}")
    return documents

# Load and process documents
text_folder = "./pa"
docs = load_texts(text_folder)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_splits = text_splitter.split_documents(docs)
valid_splits = [doc for doc in all_splits if doc.page_content.strip()]
vector_store.add_documents(documents=valid_splits)

# Load the prompt template
prompt = hub.pull("rlm/rag-prompt")

# Define the state structure
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

# Retrieval function
def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}

# Generation function
def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}

# Build the state graph
graph_builder = StateGraph(State).add_sequence([retrieve, generate])
graph_builder.add_edge(START, "retrieve")
graph = graph_builder.compile()

# Streamlit UI
st.title("💬 LangChain Chatbot")

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I assist you today?"}]

# Display message history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message(msg["role"], avatar="🧑‍💻").write(msg["content"])
    else:
        st.chat_message(msg["role"], avatar="🤖").write(msg["content"])

# Generator for streaming tokens
def generate_response(question):
    response = graph.invoke({"question": question})
    return response['answer']

# Chat input
if user_input := st.chat_input("Ask me anything:"):
    # Append user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user", avatar="🧑‍💻").write(user_input)

    # Generate response
    response_content = generate_response(user_input)
    st.chat_message("assistant", avatar="🤖").write(response_content)

    # Append assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response_content})
