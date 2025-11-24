"""
Specialized Agents for Bates Technical College

This module contains specialized agents that handle different aspects of student inquiries:
- AdmissionsAgent: Handles admission requirements, applications, and enrollment
- AcademicsAgent: Handles programs, courses, and academic information
- FinancialAidAgent: Handles financial aid, scholarships, and payment information
"""

import logging
from typing import Dict, Any, Optional
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from .rag_loader import rag_search
from .observability import BatesLogger, BatesMetrics
import pypdf
import os

# Initialize logging and metrics first
logger = BatesLogger.get_logger(__name__)
metrics = BatesMetrics()

# Vector search integration (optional)
try:
    from .vector_search import semantic_catalog_search, search_program_costs
    VECTOR_SEARCH_AVAILABLE = True
    logger.info("Vector search tools loaded for specialized agents")
except ImportError as e:
    VECTOR_SEARCH_AVAILABLE = False
    logger.warning(f"Vector search not available for specialized agents: {e}")

# PDF Path
PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "BatesTech2025-26Catalog.pdf")

class AdmissionsAgent:
    """Specialized agent for handling admissions-related queries"""
    
    def __init__(self):
        self.agent = Agent(
            name="admissions_specialist",
            model="gemini-2.0-flash",
            description="Bates Technical College Admissions Specialist",
            instruction=(
                "You are an expert admissions counselor for Bates Technical College. "
                "You specialize in:\n"
                "• Admission requirements and prerequisites\n"
                "• Application processes and deadlines\n"
                "• Placement testing and assessment\n"
                "• Registration procedures\n"
                "• Student orientation information\n"
                "• Transfer credit evaluations\n\n"
                "Always provide specific, accurate information from the catalog. "
                "If you need more details, use the available tools to search the catalog."
            ),
            tools=[
                FunctionTool(self.search_admissions_info),
                rag_search
            ]
        )
        
    def search_admissions_info(self, query: str) -> Dict[str, Any]:
        """
        Search for admissions-specific information in the Bates catalog.
        
        Args:
            query (str): Admissions-related query
            
        Returns:
            Dict[str, Any]: Search results with admissions information
        """
        try:
            logger.info(f"AdmissionsAgent searching for: {query}")
            metrics.increment_counter("admissions_searches")
            
            reader = pypdf.PdfReader(PDF_PATH)
            admissions_keywords = [
                "admission", "application", "prerequisite", "requirement", 
                "registration", "enrollment", "placement", "assessment", 
                "transcript", "GPA", "testing", "orientation"
            ]
            
            relevant_content = []
            query_lower = query.lower()
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                text_lower = text.lower()
                
                # Score based on query terms and admissions keywords
                score = text_lower.count(query_lower)
                for keyword in admissions_keywords:
                    if keyword in text_lower:
                        score += 1
                
                if score > 0:
                    relevant_content.append({
                        "page": page_num + 1,
                        "score": score,
                        "content": text[:1200]
                    })
            
            # Sort by relevance score
            relevant_content.sort(key=lambda x: x["score"], reverse=True)
            
            if relevant_content:
                top_results = relevant_content[:3]
                result_text = "\n\n".join([
                    f"Page {item['page']}: {item['content']}" 
                    for item in top_results
                ])
                
                return {
                    "status": "success",
                    "agent": "AdmissionsAgent",
                    "query": query,
                    "results": result_text,
                    "pages_found": len(relevant_content)
                }
            else:
                return {
                    "status": "no_results",
                    "agent": "AdmissionsAgent",
                    "message": "No specific admissions information found for this query."
                }
                
        except Exception as e:
            logger.error(f"AdmissionsAgent search error: {e}")
            metrics.increment_counter("admissions_errors")
            return {"status": "error", "message": str(e)}

class AcademicsAgent:
    """Specialized agent for handling academic program and course queries"""
    
    def __init__(self):
        self.agent = Agent(
            name="academics_specialist", 
            model="gemini-2.0-flash",
            description="Bates Technical College Academics Specialist",
            instruction=(
                "You are an expert academic advisor for Bates Technical College. "
                "You specialize in:\n"
                "• Academic programs and certificates\n"
                "• Course descriptions and requirements\n"
                "• Program pathways and sequencing\n"
                "• Career outcomes and job placement\n"
                "• Industry certifications and credentials\n"
                "• Academic policies and procedures\n\n"
                "Provide detailed information about programs, courses, and academic pathways. "
                "Help students understand program requirements and career opportunities."
            ),
            tools=[
                FunctionTool(self.search_academic_info),
                rag_search
            ]
        )
    
    def search_academic_info(self, query: str) -> Dict[str, Any]:
        """
        Search for academic program and course information.
        
        Args:
            query (str): Academic-related query
            
        Returns:
            Dict[str, Any]: Search results with academic information
        """
        try:
            logger.info(f"AcademicsAgent searching for: {query}")
            metrics.increment_counter("academics_searches")
            
            reader = pypdf.PdfReader(PDF_PATH)
            academic_keywords = [
                "program", "course", "certificate", "degree", "curriculum",
                "credit", "semester", "quarter", "lab", "practicum", 
                "internship", "capstone", "competency", "outcome", "career"
            ]
            
            relevant_content = []
            query_lower = query.lower()
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                text_lower = text.lower()
                
                # Enhanced scoring for academic content
                score = text_lower.count(query_lower) * 2
                for keyword in academic_keywords:
                    if keyword in text_lower:
                        score += 1
                
                # Look for program codes and course numbers
                if any(char.isdigit() for char in query) and any(char.isdigit() for char in text):
                    score += 2
                    
                if score > 1:
                    relevant_content.append({
                        "page": page_num + 1,
                        "score": score,
                        "content": text[:1200]
                    })
            
            relevant_content.sort(key=lambda x: x["score"], reverse=True)
            
            if relevant_content:
                top_results = relevant_content[:3]
                result_text = "\n\n".join([
                    f"Page {item['page']}: {item['content']}" 
                    for item in top_results
                ])
                
                return {
                    "status": "success",
                    "agent": "AcademicsAgent",
                    "query": query,
                    "results": result_text,
                    "pages_found": len(relevant_content)
                }
            else:
                return {
                    "status": "no_results",
                    "agent": "AcademicsAgent", 
                    "message": "No specific academic information found for this query."
                }
                
        except Exception as e:
            logger.error(f"AcademicsAgent search error: {e}")
            metrics.increment_counter("academics_errors")
            return {"status": "error", "message": str(e)}

class FinancialAidAgent:
    """Specialized agent for handling financial aid and payment queries"""
    
    def __init__(self):
        # Import the current costs tool
        from .enhanced_tools import current_costs_tool
        
        self.agent = Agent(
            name="financial_aid_specialist",
            model="gemini-2.0-flash", 
            description="Bates Technical College Financial Aid Specialist",
            instruction=(
                "You are an expert financial aid counselor for Bates Technical College. "
                "You specialize in:\n"
                "• Financial aid programs and eligibility\n"
                "• Scholarship opportunities and applications\n"
                "• Current tuition costs and program fees\n"
                "• Payment plans and billing options\n"
                "• Work-study programs and opportunities\n"
                "• Veterans benefits and military assistance\n"
                "• FAFSA and financial aid application processes\n\n"
                "IMPORTANT: When students ask about costs or tuition, ALWAYS use the "
                "'get_current_program_costs' tool to search for the most up-to-date "
                "information from the Bates website. The catalog may not have current prices.\n\n"
                "Help students understand their financial options and guide them "
                "through the financial aid process with current, accurate information."
            ),
            tools=[
                FunctionTool(self.search_financial_info),
                current_costs_tool,  # Added current cost search tool
                rag_search
            ]
        )
    
    def search_financial_info(self, query: str) -> Dict[str, Any]:
        """
        Search for financial aid and payment information.
        
        Args:
            query (str): Financial-related query
            
        Returns:
            Dict[str, Any]: Search results with financial information
        """
        try:
            logger.info(f"FinancialAidAgent searching for: {query}")
            metrics.increment_counter("financial_searches")
            
            reader = pypdf.PdfReader(PDF_PATH)
            financial_keywords = [
                "financial", "aid", "scholarship", "grant", "loan", "tuition", 
                "fee", "cost", "payment", "fafsa", "pell", "work-study",
                "veteran", "military", "billing", "refund", "discount"
            ]
            
            relevant_content = []
            query_lower = query.lower()
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                text_lower = text.lower()
                
                # Prioritize financial content
                score = text_lower.count(query_lower) * 2
                for keyword in financial_keywords:
                    if keyword in text_lower:
                        score += 2  # Higher weight for financial keywords
                
                # Look for dollar amounts
                if "$" in text:
                    score += 1
                    
                if score > 1:
                    relevant_content.append({
                        "page": page_num + 1,
                        "score": score,
                        "content": text[:1200]
                    })
            
            relevant_content.sort(key=lambda x: x["score"], reverse=True)
            
            if relevant_content:
                top_results = relevant_content[:3]
                result_text = "\n\n".join([
                    f"Page {item['page']}: {item['content']}" 
                    for item in top_results
                ])
                
                return {
                    "status": "success",
                    "agent": "FinancialAidAgent",
                    "query": query,
                    "results": result_text,
                    "pages_found": len(relevant_content)
                }
            else:
                return {
                    "status": "no_results",
                    "agent": "FinancialAidAgent",
                    "message": "No specific financial aid information found for this query."
                }
                
        except Exception as e:
            logger.error(f"FinancialAidAgent search error: {e}")
            metrics.increment_counter("financial_errors")
            return {"status": "error", "message": str(e)}

# Initialize specialized agents
admissions_agent = AdmissionsAgent()
academics_agent = AcademicsAgent()
financial_aid_agent = FinancialAidAgent()