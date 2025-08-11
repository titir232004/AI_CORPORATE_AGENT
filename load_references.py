import os
import re
import json
import time
from pathlib import Path
from typing import Set, List
import requests
from PyPDF2 import PdfReader
from docx import Document as DocxDocument


try:
    from langchain_community.chat_models import ChatOpenAI
    from langchain.chat_models import ChatOpenAI
    from langchain_community.document_loaders import PyPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS
    LANGCHAIN_AVAILABLE = True
except Exception:
    LANGCHAIN_AVAILABLE = False

PDF_PATH = "Data Sources.pdf"
TEMPLATE_DIR = Path("templates")
TEMPLATE_INDEX = Path("templates_texts.json")
VECTOR_DB_DIR = Path("adgm_faiss_index")


def extract_links_from_pdf(pdf_path: str) -> Set[str]:
    reader = PdfReader(pdf_path)
    urls = set()
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
            found = re.findall(r"(https?://[^\s)>\]]+)", text)
            for u in found:
                urls.add(u.strip().rstrip(',.'))
        except Exception:
            continue
    return urls


def download_file(url: str, dest: Path, timeout=15) -> bool:
    headers = {"User-Agent": "ADGM-Corporate-Agent/1.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            dest.write_bytes(resp.content)
            return True
    except Exception as e:
        print(f"Download failed for {url}: {e}")
    return False


def download_docx_templates(urls: Set[str]) -> List[Path]:
    TEMPLATE_DIR.mkdir(exist_ok=True)
    downloaded = []
    for url in urls:
        low = url.lower()
        if low.endswith(".docx"):
            fname = url.split("?")[0].split("/")[-1]
            dest = TEMPLATE_DIR / fname
            if dest.exists():
                print(f"Already downloaded: {dest}")
                downloaded.append(dest)
                continue
            print(f"Downloading {url} -> {dest}")
            ok = download_file(url, dest)
            if ok:
                downloaded.append(dest)
            else:
                print(f"Failed: {url}")
    return downloaded


def docx_to_text(path: Path) -> str:
    doc = DocxDocument(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paragraphs)


def build_templates_index(docx_paths: List[Path]):
    index = {}
    for p in docx_paths:
        try:
            text = docx_to_text(p)
            index[str(p)] = text
        except Exception as e:
            print(f"Failed to parse {p}: {e}")
    TEMPLATE_INDEX.write_text(json.dumps(index, indent=2))
    print(f"Saved templates index to {TEMPLATE_INDEX}")
    return index


def build_vector_db(pdf_path: str = PDF_PATH, templates_index: dict = None):
    if not LANGCHAIN_AVAILABLE:
        print("LangChain / embeddings not available; skipping vector DB creation.")
        return False

    print("Building vector DB using LangChain + OpenAI embeddings (requires API keys).")
    loader = PyPDFLoader(pdf_path)
    pdf_docs = loader.load()
    # Convert templates into the same format LangChain expects
    docs = list(pdf_docs)
    if templates_index:
        for src, text in templates_index.items():
            docs.append(type(pdf_docs[0])(
                page_content=text,
                metadata={"source": src}
            ))
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    VECTOR_DB_DIR.mkdir(exist_ok=True)
    vectorstore.save_local(str(VECTOR_DB_DIR))
    print(f"Saved vector DB to {VECTOR_DB_DIR}")
    return True


if __name__ == "__main__":
    if not Path(PDF_PATH).exists():
        print(f"ERROR: {PDF_PATH} not found. Put Data Sources.pdf next to this script.")
        raise SystemExit(1)

    print("Extracting links from PDF...")
    links = extract_links_from_pdf(PDF_PATH)
    print(f"Found {len(links)} links in the PDF.")

    print("Filtering and downloading .docx templates (if any)...")
    docx_files = download_docx_templates(links)
    if not docx_files:
        print("No .docx links found or downloads failed. You can still proceed with PDF-only RAG.")
    else:
        print(f"Downloaded {len(docx_files)} templates.")

    print("Building template text index...")
    templates_index = build_templates_index(docx_files)

    print("Attempting to build vector DB (optional, needs LangChain + OpenAI API keys).")
    ok = build_vector_db(PDF_PATH, templates_index)
    if ok:
        print("Reference DB built successfully.")
    else:
        print("Reference DB not built (LangChain/Embeddings unavailable). Templates JSON still created.")