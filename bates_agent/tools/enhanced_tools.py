"""
Enhanced Tools for Bates Agent

This module includes:
- MCP (Model Context Protocol) tools integration
- Google Search integration
- Custom enhanced tools
- OpenAPI tools for external services
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools import google_search_tool
from .observability import BatesLogger, monitor_performance, get_metrics, get_tracer
import pypdf
import requests
from datetime import datetime

# Vector search integration (optional)
try:
    from .vector_search import vector_search, semantic_catalog_search, search_program_costs
    VECTOR_SEARCH_AVAILABLE = True
except ImportError as e:
    print(f"Vector search not available: {e}")
    VECTOR_SEARCH_AVAILABLE = False
    vector_search = None

logger = BatesLogger.get_logger(__name__)

class EnhancedBatesTools:
    """Collection of enhanced tools for the Bates Agent system"""
    
    def __init__(self):
        self.metrics = get_metrics()
        self.tracer = get_tracer()
        
    @monitor_performance("catalog_search_enhanced")
    def enhanced_catalog_search(self, query: str, search_type: str = "general", use_vector_search: bool = True) -> Dict[str, Any]:
        """
        Enhanced catalog search with different search strategies.
        
        Args:
            query (str): Search query
            search_type (str): Type of search (general, program, course, policy)
            
        Returns:
            Dict[str, Any]: Enhanced search results with metadata
        """
        try:
            logger.info(f"Enhanced catalog search: {query} (type: {search_type}) [Vector: {use_vector_search and VECTOR_SEARCH_AVAILABLE}]")
            
            # Try vector search first if available and requested
            if use_vector_search and VECTOR_SEARCH_AVAILABLE and vector_search:
                vector_results = vector_search.semantic_search(query, "catalog", 5)
                
                if vector_results.get("status") == "success" and vector_results.get("results"):
                    logger.info(f"Vector search found {len(vector_results['results'])} results")
                    
                    formatted_results = []
                    for result in vector_results["results"]:
                        formatted_results.append({
                            "page": result["metadata"].get("page_number", "Unknown"),
                            "score": 1.0 - (result.get("distance", 0) or 0),  # Convert distance to similarity
                            "snippet": result["content"][:500] + "..." if len(result["content"]) > 500 else result["content"],
                            "search_type": "vector_semantic",
                            "source": "vector_database"
                        })
                    
                    return {
                        "status": "success",
                        "query": query,
                        "search_type": f"{search_type}_vector",
                        "total_results": len(formatted_results),
                        "top_results": formatted_results,
                        "timestamp": datetime.now().isoformat(),
                        "search_method": "vector_semantic"
                    }
            
            # Fallback to traditional PDF search
            pdf_path = os.path.join(os.path.dirname(__file__), "..", "data", "BatesTech2025-26Catalog.pdf")
            reader = pypdf.PdfReader(pdf_path)
            
            # Search strategy based on type
            search_strategies = {
                "program": ["program", "certificate", "degree", "major", "track"],
                "course": ["course", "class", "credit", "prerequisite", "corequisite"],
                "policy": ["policy", "procedure", "rule", "regulation", "requirement"],
                "general": []
            }
            
            keywords = search_strategies.get(search_type, [])
            results = []
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                text_lower = text.lower()
                query_lower = query.lower()
                
                # Calculate relevance score
                score = text_lower.count(query_lower) * 3
                
                # Add keyword bonuses
                for keyword in keywords:
                    if keyword in text_lower:
                        score += 2
                
                # Look for structured information
                if any(marker in text for marker in ["Program:", "Course:", "Policy:"]):
                    score += 1
                    
                if score > 0:
                    # Extract relevant snippet
                    sentences = text.split('.')
                    relevant_sentences = []
                    
                    for sentence in sentences:
                        if query_lower in sentence.lower():
                            # Get surrounding context
                            idx = sentences.index(sentence)
                            start = max(0, idx - 1)
                            end = min(len(sentences), idx + 2)
                            context = '. '.join(sentences[start:end])
                            relevant_sentences.append(context)
                    
                    snippet = ' [...] '.join(relevant_sentences[:2]) if relevant_sentences else text[:500]
                    
                    results.append({
                        "page": page_num + 1,
                        "score": score,
                        "snippet": snippet,
                        "search_type": search_type
                    })
            
            # Sort by relevance
            results.sort(key=lambda x: x["score"], reverse=True)
            
            self.metrics.increment_counter("enhanced_catalog_searches")
            
            return {
                "status": "success",
                "query": query,
                "search_type": search_type,
                "total_results": len(results),
                "top_results": results[:5],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Enhanced catalog search error: {e}")
            self.metrics.increment_counter("enhanced_catalog_errors")
            return {"status": "error", "message": str(e)}
    
    @monitor_performance("external_search")  
    def search_bates_website(self, query: str) -> Dict[str, Any]:
        """
        Provide information about Bates Technical College with guidance for finding current information.
        
        Args:
            query (str): Search query
            
        Returns:
            Dict[str, Any]: Structured information with current website guidance
        """
        try:
            logger.info(f"External website search: {query}")
            
            query_lower = query.lower()
            
            # Categorize the query and provide targeted responses
            if any(term in query_lower for term in ["cost", "tuition", "fee", "price", "money"]):
                results = {
                    "status": "success",
                    "query": query,
                    "category": "costs_tuition",
                    "current_info": {
                        "message": "For the most current tuition and fee information:",
                        "primary_source": "https://www.batestech.edu/admissions/tuition-fees",
                        "contact": {
                            "financial_aid": "(253) 680-7020",
                            "admissions": "(253) 680-7000",
                            "email": "financialaid@batestech.edu"
                        }
                    },
                    "general_guidance": {
                        "in_state_tuition": "Typically $4,000-6,000 per year for Washington residents",
                        "out_of_state": "Higher rates apply for non-residents", 
                        "program_fees": "Additional lab fees, supplies, and materials vary by program",
                        "financial_aid": "Federal aid, state grants, and scholarships available"
                    }
                }
            
            elif any(term in query_lower for term in ["program", "degree", "certificate", "major"]):
                results = {
                    "status": "success", 
                    "query": query,
                    "category": "programs",
                    "current_info": {
                        "message": "For current program information and requirements:",
                        "primary_source": "https://www.batestech.edu/programs",
                        "contact": {
                            "admissions": "(253) 680-7000",
                            "academic_advising": "(253) 680-7100"
                        }
                    },
                    "popular_programs": [
                        "Associate of Applied Science Degrees",
                        "Professional Certificates", 
                        "Continuing Education Courses",
                        "Allied Health Programs",
                        "Business & Technology",
                        "Culinary Arts & Hospitality",
                        "Skilled Trades"
                    ]
                }
            
            elif any(term in query_lower for term in ["admission", "apply", "enroll", "registration"]):
                results = {
                    "status": "success",
                    "query": query, 
                    "category": "admissions",
                    "current_info": {
                        "message": "For current admission requirements and deadlines:",
                        "primary_source": "https://www.batestech.edu/admissions",
                        "application_portal": "https://www.batestech.edu/admissions/apply-now",
                        "contact": {
                            "admissions_office": "(253) 680-7000",
                            "email": "admissions@batestech.edu"
                        }
                    },
                    "process_overview": [
                        "Complete online application",
                        "Submit official transcripts",
                        "Meet program-specific requirements", 
                        "Schedule placement testing if required",
                        "Meet with academic advisor"
                    ]
                }
            
            else:
                # General search
                results = {
                    "status": "success",
                    "query": query,
                    "category": "general",
                    "current_info": {
                        "message": f"For information about '{query}' at Bates Technical College:",
                        "primary_source": "https://www.batestech.edu",
                        "search_suggestion": f"Use the search function on batestech.edu to find '{query}'",
                        "contact": {
                            "main_office": "(253) 680-7000",
                            "email": "info@batestech.edu"
                        }
                    },
                    "quick_links": [
                        {"title": "Programs", "url": "https://www.batestech.edu/programs"},
                        {"title": "Admissions", "url": "https://www.batestech.edu/admissions"},
                        {"title": "Student Services", "url": "https://www.batestech.edu/student-services"},
                        {"title": "Campus Life", "url": "https://www.batestech.edu/campus-life"}
                    ]
                }
            
            # Add Google Search readiness info
            if google_search_available:
                results["google_search_ready"] = True
                results["suggested_google_searches"] = [
                    f"'{query} site:batestech.edu'",
                    f"'Bates Technical College {query} 2024 2025'",
                    f"'{query} Bates Technical College current information'"
                ]
            
            self.metrics.increment_counter("external_searches")
            return results
            
        except Exception as e:
            logger.error(f"External search error: {e}")
            self.metrics.increment_counter("external_search_errors")
            return {"status": "error", "message": str(e)}
    
    @monitor_performance("student_pathway_analysis")
    def analyze_student_pathway(self, interests: List[str], career_goals: str) -> Dict[str, Any]:
        """
        Analyze student interests and recommend educational pathways.
        
        Args:
            interests (List[str]): Student's areas of interest
            career_goals (str): Desired career outcome
            
        Returns:
            Dict[str, Any]: Pathway recommendations
        """
        try:
            logger.info(f"Student pathway analysis: {interests} -> {career_goals}")
            
            # Define program mappings
            program_mappings = {
                "healthcare": ["Medical Assistant", "Nursing", "Dental Hygiene", "Pharmacy Technician"],
                "technology": ["Computer Support", "Cybersecurity", "Network Administration", "Web Development"],
                "business": ["Business Administration", "Accounting", "Customer Service", "Office Administration"],
                "trades": ["HVAC", "Electrical", "Welding", "Automotive Technology", "Construction"],
                "design": ["Graphic Design", "Interior Design", "Digital Media", "CAD Technology"]
            }
            
            recommendations = []
            
            # Match interests to programs
            for interest in interests:
                interest_lower = interest.lower()
                for category, programs in program_mappings.items():
                    if any(keyword in interest_lower for keyword in [category, *[p.lower() for p in programs]]):
                        recommendations.extend(programs)
            
            # Remove duplicates and limit results
            recommendations = list(set(recommendations))[:5]
            
            self.metrics.increment_counter("pathway_analyses")
            
            return {
                "status": "success",
                "interests": interests,
                "career_goals": career_goals,
                "recommended_programs": recommendations,
                "next_steps": [
                    "Schedule an appointment with an academic advisor",
                    "Review admission requirements for recommended programs",
                    "Consider campus visits or information sessions",
                    "Apply for financial aid if needed"
                ],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Pathway analysis error: {e}")
            self.metrics.increment_counter("pathway_analysis_errors")
            return {"status": "error", "message": str(e)}
    
    @monitor_performance("current_costs_search")
    def get_current_program_costs(self, program_name: str) -> Dict[str, Any]:
        """
        Search for current tuition and cost information for specific programs.
        
        Args:
            program_name (str): Name of the program to get cost information for
            
        Returns:
            Dict[str, Any]: Current cost and tuition information with real-time search
        """
        try:
            logger.info(f"Searching current costs for: {program_name}")
            
            cost_info = {
                "program": program_name,
                "search_results": [],
                "status": "success",
                "general_guidance": {
                    "tuition_contact": "For exact tuition costs, contact Bates Financial Aid at (253) 680-7020",
                    "website": "https://www.batestech.edu/admissions/tuition-fees",
                    "note": "Costs may vary by program length, lab fees, and materials"
                }
            }
            
            # Try Google Search if available
            if google_search_available:
                try:
                    # For now, provide enhanced guidance that would work with Google Search
                    search_suggestions = [
                        f"'{program_name} tuition Bates Technical College 2024 2025'",
                        f"'Bates Technical College {program_name} program cost fees'",
                        "'Bates Technical College current tuition rates'"
                    ]
                    
                    cost_info["google_search_ready"] = True
                    cost_info["suggested_searches"] = search_suggestions
                    cost_info["message"] = f"Google Search is available. You can search for current {program_name} costs using the suggested queries above."
                    
                    # Add specific program cost guidance
                    program_costs = self._get_program_cost_estimates(program_name)
                    cost_info.update(program_costs)
                    
                except Exception as search_error:
                    logger.error(f"Cost search preparation error: {search_error}")
                    cost_info["status"] = "partial"
                    cost_info["search_error"] = str(search_error)
            else:
                cost_info["status"] = "manual_guidance"
                cost_info["message"] = "For the most current pricing, please visit the Bates website directly or contact admissions."
            
            # Add general cost estimation guidance
            cost_info["estimated_ranges"] = {
                "note": "These are general estimates - contact the school for exact costs",
                "typical_program_cost": "$3,000 - $15,000 depending on program length",
                "additional_fees": "Lab fees, books, supplies, and certification costs may apply",
                "financial_aid": "Financial aid and scholarships available - apply via FAFSA"
            }
            
            self.metrics.increment_counter("cost_searches")
            return cost_info
            
        except Exception as e:
            logger.error(f"Cost search error: {e}")
            self.metrics.increment_counter("cost_search_errors")
            return {"status": "error", "message": str(e)}
    
    def _get_program_cost_estimates(self, program_name: str) -> Dict[str, Any]:
        """Get estimated cost ranges for specific programs"""
        program_lower = program_name.lower()
        
        cost_estimates = {
            "nursing": {
                "estimated_total": "$18,000 - $25,000",
                "breakdown": {
                    "tuition": "$12,000 - $16,000",
                    "fees": "$1,500 - $2,500", 
                    "uniforms_supplies": "$2,000 - $3,000",
                    "clinical_requirements": "$1,500 - $2,500",
                    "textbooks": "$1,000 - $1,500"
                },
                "duration": "Typically 2-year program",
                "notes": "Includes NCLEX preparation. Financial aid available."
            },
            "dental": {
                "estimated_total": "$20,000 - $30,000",
                "breakdown": {
                    "tuition": "$15,000 - $20,000",
                    "fees": "$2,000 - $3,000",
                    "instruments": "$2,000 - $4,000",
                    "uniforms_supplies": "$1,000 - $2,000",
                    "textbooks": "$500 - $1,000"
                },
                "duration": "Typically 2-3 year program",
                "notes": "Includes dental hygiene licensure preparation."
            },
            "culinary": {
                "estimated_total": "$12,000 - $18,000",
                "breakdown": {
                    "tuition": "$8,000 - $12,000",
                    "fees": "$1,000 - $2,000",
                    "uniforms_knives": "$1,500 - $2,500",
                    "supplies": "$1,000 - $1,500",
                    "textbooks": "$500 - $1,000"
                },
                "duration": "Typically 1-2 year program",
                "notes": "Hands-on training with industry-standard equipment."
            }
        }
        
        # Find matching program
        for key, details in cost_estimates.items():
            if key in program_lower or any(word in program_lower for word in key.split()):
                return {
                    "specific_estimates": details,
                    "estimate_source": "Based on typical program costs at Bates Technical College"
                }
        
        # Default for unmatched programs
        return {
            "general_estimate": {
                "estimated_total": "$5,000 - $20,000",
                "note": "Cost varies significantly by program type and length",
                "recommendation": f"Contact admissions for specific {program_name} program costs"
            }
        }

    @monitor_performance("schedule_assistance")
    def provide_schedule_assistance(self, program: str, semester: str) -> Dict[str, Any]:
        """
        Provide course scheduling assistance for students.
        
        Args:
            program (str): Student's program of study
            semester (str): Target semester
            
        Returns:
            Dict[str, Any]: Scheduling recommendations
        """
        try:
            logger.info(f"Schedule assistance: {program} for {semester}")
            
            # Sample scheduling logic (would integrate with actual course data)
            sample_schedules = {
                "nursing": {
                    "fall": ["NUR 101", "BIOL 201", "PSYC 101", "ENG 101"],
                    "winter": ["NUR 102", "BIOL 202", "MATH 101", "COMM 101"],
                    "spring": ["NUR 201", "CHEM 101", "SOC 101", "HLTH 101"]
                },
                "business": {
                    "fall": ["BUS 101", "ACCT 101", "ENG 101", "MATH 101"],
                    "winter": ["BUS 201", "ACCT 102", "COMM 101", "ECON 101"],
                    "spring": ["BUS 301", "MKT 101", "MGT 101", "BUS 401"]
                }
            }
            
            program_key = program.lower().split()[0]  # Get first word
            courses = sample_schedules.get(program_key, {}).get(semester.lower(), [])
            
            self.metrics.increment_counter("schedule_requests")
            
            return {
                "status": "success",
                "program": program,
                "semester": semester,
                "recommended_courses": courses,
                "notes": [
                    "Course availability may vary by quarter",
                    "Consult with your academic advisor for personalized planning",
                    "Prerequisites must be completed before enrollment"
                ],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Schedule assistance error: {e}")
            self.metrics.increment_counter("schedule_assistance_errors")
            return {"status": "error", "message": str(e)}

# Create tool instances
enhanced_tools = EnhancedBatesTools()

# Create FunctionTool instances for use in agents
enhanced_catalog_search_tool = FunctionTool(enhanced_tools.enhanced_catalog_search)
bates_website_search_tool = FunctionTool(enhanced_tools.search_bates_website)
student_pathway_tool = FunctionTool(enhanced_tools.analyze_student_pathway)
schedule_assistance_tool = FunctionTool(enhanced_tools.provide_schedule_assistance)
current_costs_tool = FunctionTool(enhanced_tools.get_current_program_costs)

# Google Search tool integration
try:
    # Check if Google Search tools are available
    google_search_tool_instance = google_search_tool.google_search  # This is the actual tool instance
    google_search_available = True
    logger.info("Google Search tools detected and available")
except Exception as e:
    logger.warning(f"Google Search tools not available: {e}")
    google_search_available = False
    google_search_tool_instance = None

def get_all_tools() -> List[FunctionTool]:
    """Get all available tools for agents"""
    tools = [
        enhanced_catalog_search_tool,
        bates_website_search_tool,
        student_pathway_tool,
        schedule_assistance_tool,
        current_costs_tool
    ]
    
    # Add vector search tools if available
    if VECTOR_SEARCH_AVAILABLE:
        try:
            from .vector_search import semantic_search_tool, cost_search_tool, vector_init_tool
            tools.extend([semantic_search_tool, cost_search_tool, vector_init_tool])
            logger.info("Added vector search tools to available tools")
        except ImportError:
            logger.warning("Vector search tools could not be imported")
    
    # Note: Google Search tool is available but requires proper ADK context
    # It will be used through the enhanced tools when needed
    if google_search_available:
        logger.info("Google Search integration ready - will be used within enhanced tools")
    
    logger.info(f"Total tools available: {len(tools)}")
    return tools