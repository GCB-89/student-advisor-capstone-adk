"""
Vector Database Integration for Bates Agent
Using ChromaDB for local vector storage and semantic search
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import pypdf
from sentence_transformers import SentenceTransformer
from google.adk.tools import FunctionTool
from .observability import BatesLogger, monitor_performance

logger = BatesLogger.get_logger(__name__)

class BatesVectorSearch:
    """Vector database for semantic search of Bates Technical College information"""
    
    def __init__(self, persist_directory: str = "vector_db"):
        self.persist_directory = os.path.join(os.path.dirname(__file__), "..", "data", persist_directory)
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize collections
        self.catalog_collection = self._get_or_create_collection("bates_catalog")
        self.costs_collection = self._get_or_create_collection("bates_costs") 
        self.programs_collection = self._get_or_create_collection("bates_programs")
        
        # Initialize embedding model
        self.embedding_model = None
        logger.info("Vector search initialized (embedding model will load on first use)")
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        try:
            return self.client.get_collection(name)
        except:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
    def _get_embedding_model(self):
        """Lazy load the embedding model only when actually needed"""
        if self.embedding_model is None:
            try:
                logger.info("Loading SentenceTransformer model (first use)...")
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✓ Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"Could not load SentenceTransformer: {e}")
                self.embedding_model = None
        return self.embedding_model
    
    @monitor_performance("catalog_indexing")
    def index_catalog_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Index the Bates catalog PDF into vector database
        
        Args:
            pdf_path: Path to the catalog PDF
            
        Returns:
            Dict with indexing results
        """
        try:
            if not os.path.exists(pdf_path):
                return {"status": "error", "message": "PDF file not found"}
            
            logger.info(f"Indexing catalog PDF: {pdf_path}")
            
            reader = pypdf.PdfReader(pdf_path)
            documents = []
            metadatas = []
            ids = []
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                
                if len(text.strip()) < 50:  # Skip mostly empty pages
                    continue
                
                # Split into chunks for better search
                chunks = self._split_text_into_chunks(text, max_chunk_size=1000)
                
                for chunk_idx, chunk in enumerate(chunks):
                    if len(chunk.strip()) < 100:  # Skip very small chunks
                        continue
                    
                    doc_id = f"catalog_page_{page_num+1}_chunk_{chunk_idx}"
                    
                    documents.append(chunk)
                    metadatas.append({
                        "page_number": page_num + 1,
                        "chunk_index": chunk_idx,
                        "document_type": "catalog",
                        "source": "BatesTech2025-26Catalog.pdf"
                    })
                    ids.append(doc_id)
            
            # Add to collection in batches
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_metas = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                
                self.catalog_collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
            
            logger.info(f"Indexed {len(documents)} chunks from {len(reader.pages)} pages")
            
            return {
                "status": "success",
                "total_chunks": len(documents),
                "total_pages": len(reader.pages),
                "collection_size": self.catalog_collection.count()
            }
            
        except Exception as e:
            logger.error(f"Catalog indexing error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _split_text_into_chunks(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """Split text into overlapping chunks for better context preservation"""
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < max_chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    @monitor_performance("vector_search")
    def semantic_search(self, query: str, collection_name: str = "catalog", 
                       n_results: int = 5) -> Dict[str, Any]:
        """
        Perform semantic search across the specified collection
        
        Args:
            query: Search query
            collection_name: Which collection to search (catalog, costs, programs)
            n_results: Number of results to return
            
        Returns:
            Dict with search results
        """
        try:
            collection_map = {
                "catalog": self.catalog_collection,
                "costs": self.costs_collection,
                "programs": self.programs_collection
            }
            
            collection = collection_map.get(collection_name)
            if not collection:
                return {"status": "error", "message": f"Collection {collection_name} not found"}
            
            # Perform the search
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'][0] else {},
                        "distance": results['distances'][0][i] if results['distances'] and results['distances'][0] else None,
                        "id": results['ids'][0][i] if results['ids'][0] else None
                    }
                    formatted_results.append(result)
            
            return {
                "status": "success",
                "query": query,
                "collection": collection_name,
                "results": formatted_results,
                "total_found": len(formatted_results)
            }
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return {"status": "error", "message": str(e)}
    
    @monitor_performance("add_program_info")
    def add_program_information(self, program_name: str, description: str, 
                               cost_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Add or update program information in the vector database
        
        Args:
            program_name: Name of the program
            description: Program description
            cost_info: Optional cost information
            
        Returns:
            Dict with operation result
        """
        try:
            # Add to programs collection
            doc_id = f"program_{program_name.lower().replace(' ', '_')}"
            
            metadata = {
                "program_name": program_name,
                "document_type": "program_info",
                "last_updated": "2025-11-23"  # Could be dynamic
            }
            
            if cost_info:
                metadata.update({"has_cost_info": True})
                
                # Also add to costs collection
                cost_doc = f"Program: {program_name}\nCosts: {json.dumps(cost_info, indent=2)}\nDescription: {description}"
                cost_id = f"cost_{program_name.lower().replace(' ', '_')}"
                
                self.costs_collection.upsert(
                    documents=[cost_doc],
                    metadatas=[{**metadata, "document_type": "cost_info"}],
                    ids=[cost_id]
                )
            
            self.programs_collection.upsert(
                documents=[f"{program_name}: {description}"],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            return {"status": "success", "program": program_name}
            
        except Exception as e:
            logger.error(f"Add program info error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about all collections"""
        try:
            stats = {
                "catalog_documents": self.catalog_collection.count(),
                "cost_documents": self.costs_collection.count(),
                "program_documents": self.programs_collection.count(),
                "total_documents": (
                    self.catalog_collection.count() + 
                    self.costs_collection.count() + 
                    self.programs_collection.count()
                )
            }
            return stats
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"error": str(e)}

# Initialize vector search instance
vector_search = BatesVectorSearch()

# Function tool wrappers
def semantic_catalog_search(query: str, max_results: int = 5) -> str:
    """Search the Bates catalog using semantic similarity"""
    result = vector_search.semantic_search(query, "catalog", max_results)
    
    if result["status"] == "success" and result["results"]:
        formatted = f"Found {len(result['results'])} relevant results for '{query}':\n\n"
        
        for i, res in enumerate(result["results"], 1):
            page = res["metadata"].get("page_number", "Unknown")
            content = res["content"][:300] + "..." if len(res["content"]) > 300 else res["content"]
            formatted += f"{i}. (Page {page}) {content}\n\n"
        
        return formatted
    else:
        return f"No results found for '{query}'. {result.get('message', '')}"

def search_program_costs(query: str) -> str:
    """Search for program cost information using vector similarity"""
    result = vector_search.semantic_search(query, "costs", 3)
    
    if result["status"] == "success" and result["results"]:
        formatted = f"Cost information for '{query}':\n\n"
        
        for res in result["results"]:
            formatted += f"• {res['content']}\n\n"
        
        return formatted
    else:
        return f"No cost information found for '{query}'. Please contact admissions for current pricing."

def initialize_vector_database() -> str:
    """Initialize the vector database with catalog content"""
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "data", "BatesTech2025-26Catalog.pdf")
    
    if not os.path.exists(pdf_path):
        return "Catalog PDF not found. Please ensure the catalog file is available."
    
    # Check if already indexed
    stats = vector_search.get_collection_stats()
    if stats.get("catalog_documents", 0) > 0:
        return f"Vector database already initialized with {stats['catalog_documents']} catalog documents."
    
    result = vector_search.index_catalog_pdf(pdf_path)
    
    if result["status"] == "success":
        return f"Successfully indexed {result['total_chunks']} chunks from {result['total_pages']} pages."
    else:
        return f"Failed to initialize vector database: {result.get('message', 'Unknown error')}"

# Create FunctionTool instances
semantic_search_tool = FunctionTool(semantic_catalog_search)
cost_search_tool = FunctionTool(search_program_costs)
vector_init_tool = FunctionTool(initialize_vector_database)