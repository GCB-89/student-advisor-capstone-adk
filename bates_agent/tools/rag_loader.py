import os
from google.adk.tools.function_tool import FunctionTool

# Import vector search to use ChromaDB instead of reading PDF every time
try:
    from .vector_search import vector_search
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False

def load_bates_catalog(query: str) -> dict:
    """
    Searches the Bates Technical College catalog using vector database.
    
    Args:
        query (str): The search query to find relevant information in the catalog
        
    Returns:
        dict: A dictionary containing the search status and relevant catalog content
    """
    try:
        # Use ChromaDB vector search (FAST - already indexed!)
        if VECTOR_AVAILABLE and vector_search:
            results = vector_search.semantic_search(query, "catalog", 5)
            
            if results.get("status") == "success" and results.get("results"):
                formatted_text = ""
                for i, res in enumerate(results["results"], 1):
                    page = res["metadata"].get("page_number", "Unknown")
                    content = res["content"]
                    formatted_text += f"\n[Page {page}]: {content}\n"
                
                return {
                    "status": "success",
                    "result": f"USER QUERY: {query}\n\nRELEVANT CATALOG CONTENT:{formatted_text}"
                }
        
        # Fallback message if vector search not available
        return {
            "status": "error", 
            "message": "Vector search not available. Please use semantic_catalog_search tool instead."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

rag_search = FunctionTool(load_bates_catalog)