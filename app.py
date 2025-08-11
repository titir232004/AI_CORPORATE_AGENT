import streamlit as st
from docx import Document
from io import BytesIO
import tempfile
import json
from classify_docs import classify_document, best_effort_title
from checklists import checklists
from detect_flags import detect_red_flags
from comment_doc import insert_comments
from load_references import build_vector_db, TEMPLATE_INDEX, TEMPLATE_DIR, PDF_PATH

st.set_page_config(page_title="ADGM Corporate Agent", layout="wide")
st.title("📄 ADGM Corporate Agent — Demo")

with st.sidebar:
    st.header("Reference DB")
    if st.button("(Re)build references (downloads + DB)"):
        st.info("Running load_references.py process. Check the terminal for progress.")
        import subprocess, sys
        subprocess.run([sys.executable, "load_references.py"])
        st.success("Done (see terminal logs).")

st.markdown("Upload one or more `.docx` documents to analyze for ADGM incorporation compliance.")

uploaded = st.file_uploader("Upload .docx files", type="docx", accept_multiple_files=True)

if uploaded:
    docs_info = []
    for f in uploaded:
        try:
            b = f.read()
            doc = Document(BytesIO(b))
            text = "\n".join([p.text for p in doc.paragraphs if p.text and p.text.strip()])
        except Exception as e:
            st.error(f"Failed to parse {f.name}: {e}")
            text = ""

        doc_type = classify_document(text)
        title = best_effort_title(text) or f.name
        docs_info.append({"filename": f.name, "type": doc_type, "text": text, "fileobj": BytesIO(b), "title": title})

    st.subheader("Detected Document Types")
    for info in docs_info:
        st.write(f"- **{info['filename']}** → {info['type']}")

    process = st.selectbox("Select process to validate against", options=list(checklists.keys()))
    required = checklists[process]
    detected_types = [d["type"] for d in docs_info]
    missing = [r for r in required if r not in detected_types]

    st.subheader("Checklist Verification")
    if missing:
        st.error(f"Missing documents for {process}: {missing}")
    else:
        st.success(f"All required documents for {process} appear present.")

    st.subheader("Document Analysis & Reviewed Files")
    summary = {"process": process, "documents_uploaded": len(docs_info), "required_documents": len(required), "missing_documents": missing, "issues_found": []}

    for info in docs_info:
        st.markdown(f"### {info['filename']} — {info['type']}")
        with st.expander("View extracted text"):
            st.text_area("Document text", value=info["text"][:10000], height=300)

        issues = detect_red_flags(info["text"], doc_name=info["filename"])
        if not issues:
            st.success("No issues detected by heuristics.")
        else:
            st.write(f"Found {len(issues)} issue(s):")
            for i, it in enumerate(issues, 1):
                st.write(f"{i}. **{it.get('issue')}** — severity: {it.get('severity')}")
                st.write(f"   suggestion: {it.get('suggestion')}")
        summary["issues_found"].extend(issues)

        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        try:
            # fileobj is BytesIO
            insert_comments(info["fileobj"], issues, tmp_out.name)
            tmp_out.flush()
            tmp_out.close()
            with open(tmp_out.name, "rb") as fh:
                st.download_button(f"⬇️ Download Reviewed {info['filename']}", fh, file_name=f"reviewed_{info['filename']}")
        except Exception as e:
            st.error(f"Failed to create reviewed doc for {info['filename']}: {e}")

    st.subheader("Structured JSON Summary")
    st.json(summary)

    # allow save summary
    if st.button("Download JSON summary"):
        st.download_button("Download JSON", json.dumps(summary, indent=2), file_name="summary.json")

else:
    st.info("Upload .docx files to get started. If you do not have templates downloaded yet, run `python load_references.py` once.")
