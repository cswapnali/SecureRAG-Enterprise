from pathlib import Path
import csv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os

load_dotenv()

def get_role_for_path(file_path: Path, data_dir: Path) -> str:
    try:
        rel_path = file_path.relative_to(data_dir)
        return rel_path.parts[0]
    except Exception:
        return "general"

def embedding_func():
    data_dir = Path(__file__).parent.parent.parent / "resources" / "data"
    data_dir = data_dir.resolve()
    
    persist_dir = Path(__file__).parent.parent.parent / "chroma_db"
    persist_dir = persist_dir.resolve()

    print(f"Scanning for data in: {data_dir}")
    print(f"Chroma DB will be saved in: {persist_dir}")

    md_docs = []
    for file in data_dir.rglob("*.md"):
        role = get_role_for_path(file, data_dir)
        text = file.read_text(encoding="utf-8")
        md_docs.append(
            Document(
                page_content=text,
                metadata={"source": str(file), "role": role}
            )
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(md_docs)

    csv_docs = []
    for file in data_dir.rglob("*.csv"):
        role = get_role_for_path(file, data_dir)
        with open(file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_text = ", ".join([f"{k}: {v}" for k, v in row.items() if v is not None])
                csv_docs.append(
                    Document(
                        page_content=row_text,
                        metadata={"source": str(file), "role": role}
                    )
                )

    all_chunks = chunks + csv_docs
    print(f"Found {len(chunks)} markdown chunks and {len(csv_docs)} CSV rows. Total: {len(all_chunks)}")

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5"
    )

    import shutil
    if persist_dir.exists():
        print("Cleaning up old database directory...")
        try:
            shutil.rmtree(persist_dir)
        except Exception as e:
            print(f"Warning: Could not remove old db directory: {e}")

    db = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=str(persist_dir)
    )

    print(f"Successfully indexed {len(all_chunks)} chunks to {persist_dir}")

    results = db.similarity_search(
        "List client applications?",
        k=3
    )

    def safe_print(text):
        try:
            print(text)
        except UnicodeEncodeError:
            try:
                print(text.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8'))
            except Exception:
                print(text.encode('ascii', errors='replace').decode('ascii'))

    safe_print("\n--- Test Query Results (List client applications?) ---")
    for doc in results:
        source_rel = Path(doc.metadata.get("source", "")).name
        role_label = doc.metadata.get("role", "None")
        safe_print(f"Source: {source_rel} | Role: {role_label}")
        safe_print(doc.page_content[:150] + "...")
        safe_print("-" * 50)
