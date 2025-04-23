import os
import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Constants ---
PDF_DIR = "app\static"  # Adjust path if needed
PDF_FILES = ["Handbook Volume 1.pdf", "Handbook Volume 2.pdf"]  # Your documents
CHUNK_SIZE = 800  # Adjust chunk size as needed
CHUNK_OVERLAP = 200

# --- Get openai api key ---
load_dotenv()  # This reads from the .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Load PDFs ---
def load_documents():
    docs = []
    for pdf in PDF_FILES:
        path = os.path.join(PDF_DIR, pdf)
        loader = PyPDFLoader(path)
        docs.extend(loader.load())
    return docs

# --- Split into chunks ---
def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    return splitter.split_documents(documents)

# --- Build FAISS DB ---
def build_vectorstore(documents):
    embeddings = OpenAIEmbeddings()
    return FAISS.from_documents(documents, embeddings)

# --- Set up the RAG chain (once) ---
documents = load_documents()
chunks = split_documents(documents)
vectorstore = build_vectorstore(chunks)
retriever = vectorstore.as_retriever()

qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0),
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)

# --- Public function ---
def get_rag_answer(query: str) -> str:
    result = qa_chain.invoke({"query": query})
    return result["result"]