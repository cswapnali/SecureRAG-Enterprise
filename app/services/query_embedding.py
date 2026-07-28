from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

def query_embedding(question: str, user_role: str = "general"):
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5"
    )

    persist_dir = Path(__file__).parent.parent.parent / "chroma_db"
    persist_dir = persist_dir.resolve()

    db = Chroma(
        persist_directory=str(persist_dir),
        embedding_function=embeddings
    )

    # Implement Role-Based Access Control filtering
    if user_role in ["c_level", "executive"]:
        # C-level executives have full access to all documents across all roles
        filter_dict = None
    else:
        allowed_roles = ["general"]
        if user_role and user_role != "general":
            allowed_roles.append(user_role)
        filter_dict = {"role": {"$in": allowed_roles}}
    
    results = db.similarity_search(
        question,
        k=4,
        filter=filter_dict
    )

    return results

