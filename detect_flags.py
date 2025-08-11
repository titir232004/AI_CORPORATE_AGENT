import json
import os
from typing import List, Dict
from pathlib import Path

TEMPLATE_INDEX = Path("templates_texts.json")
VECTOR_DB_DIR = Path("adgm_faiss_index")

# Optional langchain/llm
try:
    from langchain_community.embeddings import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain.chat_models import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except Exception:
    LANGCHAIN_AVAILABLE = False

def load_template_texts():
    if TEMPLATE_INDEX.exists():
        try:
            return json.loads(TEMPLATE_INDEX.read_text())
        except Exception:
            return {}
    return {}

def heuristic_compare(upload_text: str, template_texts: Dict[str, str]) -> List[Dict]:
    issues = []
    for src, ttext in template_texts.items():
        t_lines = [l.strip() for l in ttext.splitlines() if l.strip()]
        candidates = t_lines[:40]
        missing = []
        for c in candidates:
            if len(c) < 6:
                continue
            if c.lower() not in upload_text.lower():
                missing.append(c)
        if len(missing) > 3:
            issues.append({
                "document": os.path.basename(src),
                "section": "Multiple top sections",
                "issue": f"A number of top template sections are missing or phrased differently ({len(missing)} missing).",
                "severity": "High",
                "suggestion": "Compare your document to the official template and include missing sections. Use the ADGM template text as reference."
            })
    return issues

def detect_red_flags_from_llm(upload_text: str, k_context: int = 3) -> List[Dict]:
    if not LANGCHAIN_AVAILABLE or not VECTOR_DB_DIR.exists():
        return []

    try:
        vectorstore = FAISS.load_local(str(VECTOR_DB_DIR), OpenAIEmbeddings(), allow_dangerous_deserialization=True)
        retriever = vectorstore.as_retriever(search_kwargs={"k": k_context})
        ctx_docs = retriever.get_relevant_documents(upload_text)
        context = "\n\n".join([d.page_content for d in ctx_docs])[:4000]  # truncate
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = f"""
You are an ADGM compliance assistant. Using the provided ADGM context (rules and official templates), analyze
the following uploaded legal document and produce a JSON array of issues.

Context (ADGM rules / templates):
{context}

Uploaded document:
{upload_text}

Output format: JSON array of objects with keys:
document, section, issue, severity (High|Medium|Low), suggestion.

Only output JSON.
"""
        raw = llm.predict(prompt)
        import json, re
        json_text = raw.strip()
        m = re.search(r"(\[.*\])", json_text, re.S)
        if m:
            json_text = m.group(1)
        issues = json.loads(json_text)
        if isinstance(issues, list):
            return issues
    except Exception as e:
        print("LLM/FAISS detection failed:", e)
    return []

def detect_red_flags(upload_text: str, doc_name: str = "uploaded_doc") -> List[Dict]:
    issues = []
    templates = load_template_texts()
    if templates:
        try:
            issues.extend(heuristic_compare(upload_text, templates))
        except Exception as e:
            print("Heuristic compare error:", e)
    try:
        issues_from_llm = detect_red_flags_from_llm(upload_text)
        if issues_from_llm:
            issues.extend(issues_from_llm)
    except Exception as e:
        print("LLM detection error:", e)

    # 3) Fallback syntactic checks (jurisdiction string, signatory section)
    if "adgm" not in upload_text.lower() and "abudhabi global market" not in upload_text.lower():
        issues.append({
            "document": doc_name,
            "section": "Jurisdiction clause",
            "issue": "Jurisdiction does not explicitly reference ADGM or ADGM Courts.",
            "severity": "High",
            "suggestion": "Add a jurisdiction clause referencing ADGM (e.g. 'This Agreement is governed by the laws of ADGM, and the ADGM Courts have exclusive jurisdiction')."
        })
    if "signature" not in upload_text.lower() and "signed" not in upload_text.lower():
        issues.append({
            "document": doc_name,
            "section": "Signatory",
            "issue": "No signatory / signature block detected.",
            "severity": "High",
            "suggestion": "Add a signature block with printed name, title, date, and signature lines."
        })

    return issues
