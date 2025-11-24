import pypdf
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from typing import Dict, Any, Optional
import json

# Import enhanced components
from bates_agent.tools.rag_loader import rag_search
from bates_agent.tools.specialized_agents import (
    admissions_agent, academics_agent, financial_aid_agent
)
from bates_agent.tools.enhanced_tools import get_all_tools
from bates_agent.tools.session_memory import session_manager
from bates_agent.tools.observability import (
    BatesLogger, monitor_performance, get_metrics, get_tracer
)

# Initialize logging and monitoring
logger = BatesLogger.get_logger(__name__)
metrics = get_metrics()
tracer = get_tracer()

# Path to the Bates PDF (inside your package folder)
PDF_PATH = "bates_agent/data/BatesTech2025-26Catalog.pdf"


# ---------------------------------------------------------
# TOOL 1 — Simple Keyword Search
# ---------------------------------------------------------
def search_catalog(query: str) -> dict:
    """Search the Bates catalog PDF for matching text."""
    try:
        reader = pypdf.PdfReader(PDF_PATH)
        results = []

        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if query.lower() in text.lower():
                results.append({
                    "page": page_num + 1,
                    "excerpt": text[:500]
                })

        if not results:
            return {
                "status": "success",
                "results": [],
                "message": "No matches found in the catalog."
            }

        return {"status": "success", "results": results}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------
# TOOL 2 — RAG: Return Most Relevant Chunk
# ---------------------------------------------------------
def rag_bates(query: str) -> dict:
    """Return the most relevant chunk from the Bates catalog."""
    try:
        reader = pypdf.PdfReader(PDF_PATH)

        best_match = None
        best_score = 0

        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            # Count occurrences of query terms
            score = text.lower().count(query.lower())
            
            # Also check for partial matches of query words
            query_words = query.lower().split()
            for word in query_words:
                if len(word) > 2:  # Only count words longer than 2 characters
                    score += text.lower().count(word) * 0.5

            if score > best_score:
                best_score = score
                best_match = {
                    "page": page_num + 1,
                    "content": text[:1500]
                }

        if not best_match:
            return {"status": "success", "answer": "No matching content found."}

        return {
            "status": "success",
            "page": best_match["page"],
            "content": best_match["content"]
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------
# MULTI-AGENT ORCHESTRATOR FUNCTIONS
# ---------------------------------------------------------

@monitor_performance("agent_routing")
def route_to_specialist(query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Route queries to appropriate specialist agents based on content analysis.
    
    Args:
        query (str): Student query to route
        session_id (str, optional): Session ID for context
        
    Returns:
        Dict[str, Any]: Response from specialist agent with routing info
    """
    try:
        logger.info(f"Routing query to specialist: {query}")
        
        # Analyze query to determine routing
        query_lower = query.lower()
        
        # Routing logic based on keywords
        if any(keyword in query_lower for keyword in [
            "admission", "apply", "application", "requirement", "prerequisite", 
            "enroll", "registration", "placement", "test", "transcript"
        ]):
            specialist = "admissions"
            agent = admissions_agent.agent
            
        elif any(keyword in query_lower for keyword in [
            "program", "course", "class", "curriculum", "degree", "certificate",
            "major", "study", "academic", "credit", "semester", "quarter"
        ]):
            specialist = "academics" 
            agent = academics_agent.agent
            
        elif any(keyword in query_lower for keyword in [
            "financial", "aid", "scholarship", "grant", "loan", "tuition",
            "cost", "fee", "payment", "fafsa", "money", "afford"
        ]):
            specialist = "financial_aid"
            agent = financial_aid_agent.agent
            
        else:
            # Default to general agent for broad queries
            specialist = "general"
            agent = None
        
        # Record routing decision
        if session_id:
            session_manager.record_interaction(
                session_id, "routing", query, f"Routed to {specialist}"
            )
        
        metrics.increment_counter(f"queries_routed_to_{specialist}")
        
        return {
            "status": "success",
            "specialist": specialist,
            "agent": agent,
            "routing_confidence": "high" if agent else "low"
        }
        
    except Exception as e:
        logger.error(f"Agent routing error: {e}")
        metrics.increment_counter("routing_errors")
        return {"status": "error", "message": str(e)}

@monitor_performance("multi_agent_query")
def handle_multi_agent_query(query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Handle queries using the multi-agent system with sequential processing.
    
    Args:
        query (str): Student query
        session_id (str, optional): Session ID for memory/context
        
    Returns:
        Dict[str, Any]: Comprehensive response from multiple agents
    """
    try:
        logger.info(f"Multi-agent query processing: {query}")
        
        # Get or create session
        if not session_id:
            session_id = session_manager.create_session()
        
        # Get student context from memory
        context = session_manager.memory_bank.get_student_context(
            session_manager.get_session(session_id)["student_id"]
        )
        
        # Route to primary specialist
        routing_result = route_to_specialist(query, session_id)
        
        if routing_result["status"] == "error":
            return routing_result
        
        responses = {
            "primary_specialist": routing_result["specialist"],
            "session_id": session_id,
            "student_context": context["context_summary"],
            "responses": {}
        }
        
        # Get response from primary specialist
        if routing_result["agent"]:
            try:
                specialist_response = routing_result["agent"].run(
                    f"Student query: {query}\n\nStudent context: {context['context_summary']}"
                )
                responses["responses"][routing_result["specialist"]] = specialist_response
            except Exception as e:
                logger.error(f"Specialist {routing_result['specialist']} error: {e}")
                responses["responses"][routing_result["specialist"]] = f"Error: {e}"
        
        # For complex queries, get additional perspectives
        complex_keywords = ["program", "cost", "requirement", "pathway", "career"]
        if any(keyword in query.lower() for keyword in complex_keywords):
            
            # Get academic perspective if not primary
            if routing_result["specialist"] != "academics":
                try:
                    academic_response = academics_agent.agent.run(
                        f"Provide academic perspective on: {query}"
                    )
                    responses["responses"]["academics_perspective"] = academic_response
                except Exception as e:
                    logger.error(f"Academic perspective error: {e}")
            
            # Get financial perspective for program queries
            if "program" in query.lower() and routing_result["specialist"] != "financial_aid":
                try:
                    financial_response = financial_aid_agent.agent.run(
                        f"Provide cost/financial aid information for: {query}"
                    )
                    responses["responses"]["financial_perspective"] = financial_response
                except Exception as e:
                    logger.error(f"Financial perspective error: {e}")
        
        # Record successful multi-agent interaction
        session_manager.record_interaction(
            session_id, "multi_agent_query", query, 
            f"Processed by {len(responses['responses'])} agents"
        )
        
        metrics.increment_counter("multi_agent_queries_completed")
        
        return {
            "status": "success",
            "query": query,
            **responses
        }
        
    except Exception as e:
        logger.error(f"Multi-agent query error: {e}")
        metrics.increment_counter("multi_agent_query_errors")
        return {"status": "error", "message": str(e)}

@monitor_performance("agent_metrics")
def get_agent_metrics() -> Dict[str, Any]:
    """
    Get comprehensive metrics about agent system performance.
    
    Returns:
        Dict[str, Any]: System metrics and performance data
    """
    try:
        system_metrics = metrics.get_metrics()
        recent_traces = tracer.get_traces(limit=10)
        
        return {
            "status": "success",
            "system_metrics": system_metrics,
            "recent_traces": recent_traces,
            "active_sessions": len(session_manager.active_sessions),
            "total_students": len(session_manager.memory_bank.profiles)
        }
        
    except Exception as e:
        logger.error(f"Metrics retrieval error: {e}")
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------
# ENHANCED ROOT AGENT WITH MULTI-AGENT ORCHESTRATION
# ---------------------------------------------------------
root_agent = Agent(
    name="bates_multi_agent_orchestrator",
    model="gemini-2.0-flash",
    description="Bates Technical College Multi-Agent Advisor System",
    instruction=(
        "You are the main orchestrator for the Bates Technical College advisor system. "
        "You coordinate multiple specialist agents to provide comprehensive student support:\n\n"
        
        "🎯 **Your Capabilities:**\n"
        "• Route queries to specialist agents (Admissions, Academics, Financial Aid)\n"
        "• Coordinate multi-agent responses for complex questions\n"
        "• Maintain student context and session memory\n"
        "• Provide comprehensive, personalized advice\n\n"
        
        "🤝 **Specialist Agents:**\n"
        "• **Admissions Agent**: Application process, requirements, enrollment\n"
        "• **Academics Agent**: Programs, courses, curriculum, career pathways\n"
        "• **Financial Aid Agent**: Costs, scholarships, payment options\n\n"
        
        "📊 **Enhanced Tools:**\n"
        "• Advanced catalog search with multiple strategies\n"
        "• Student pathway analysis and recommendations\n"
        "• Schedule assistance and course planning\n"
        "• External website search for current information\n\n"
        
        "🧠 **Memory & Context:**\n"
        "• Remember student interests and previous questions\n"
        "• Track programs viewed and recommendations given\n"
        "• Provide personalized advice based on interaction history\n\n"
        
        "Always use the multi-agent system for comprehensive responses. "
        "Consider the student's context and provide actionable, specific guidance. "
        "If a question spans multiple areas, coordinate responses from relevant specialists."
    ),
    tools=[
        FunctionTool(handle_multi_agent_query),
        FunctionTool(route_to_specialist), 
        FunctionTool(get_agent_metrics),
        search_catalog, 
        rag_bates, 
        rag_search,
        *get_all_tools()  # Include all enhanced tools
    ]
)
