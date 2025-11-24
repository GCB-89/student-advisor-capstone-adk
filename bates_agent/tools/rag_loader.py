import os
import pypdf
from google.adk.tools.function_tool import FunctionTool

CATALOG_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "BatesTech2025-26Catalog.pdf"
)

def load_bates_catalog(query: str) -> dict:
    """
    Searches the Bates Technical College catalog PDF for relevant information.
    
    Args:
        query (str): The search query to find relevant information in the catalog
        
    Returns:
        dict: A dictionary containing the search status and relevant catalog content
    """
    try:
        reader = pypdf.PdfReader(CATALOG_PATH)
        text = ""
        
        # Extract text from all pages
        for page in reader.pages:
            text += page.extract_text() or ""
            
        # Simple search for query terms in the text
        query_lower = query.lower()
        relevant_sections = []
        
        # Split text into chunks and find relevant ones
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
        for i, chunk in enumerate(chunks):
            if query_lower in chunk.lower():
                relevant_sections.append(f"Section {i+1}: {chunk}")
                
        if relevant_sections:
            result_text = "\n\n".join(relevant_sections[:3])  # Limit to first 3 relevant sections
        else:
            result_text = text[:5000]  # Fallback to first 5000 characters
            
        return {
            "status": "success",
            "result": f"USER QUERY: {query}\n\nRELEVANT CATALOG CONTENT:\n{result_text}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

rag_search = FunctionTool(load_bates_catalog)
