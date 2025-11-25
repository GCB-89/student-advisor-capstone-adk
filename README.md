# 🎓 Student Advisor Capstone - ADK Implementation

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Google ADK](https://img.shields.io/badge/Google-ADK-4285F4.svg)](https://developers.google.com/adk)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/cepeda-b-41b239331)
[![Kaggle](https://img.shields.io/badge/Kaggle-20BEFF?style=flat&logo=Kaggle&logoColor=white)](https://www.kaggle.com/cepedabraxton)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/nelly-kosasih-2135b413b)
[![Kaggle](https://img.shields.io/badge/Kaggle-20BEFF?style=flat&logo=Kaggle&logoColor=white)](https://www.kaggle.com/nellykwan)



A sophisticated multi-agent AI system built with Google's Agent Development Kit (ADK) to provide comprehensive educational assistance for Bates Technical College students. This capstone project demonstrates advanced AI agent architecture with specialized routing and enhanced educational tools.

---

## 🚀 Overview

This project implements an intelligent student advisor system using Google's ADK framework. The system employs a multi-agent architecture where specialized agents handle different aspects of student inquiries, from admissions and academics to financial aid assistance.
---

## 🎬 Live Demo & Screenshots

https://github.com/user-attachments/assets/c9321c92-2c01-495a-8c5b-2f101355b6dd

### System in Action

The following screenshots further demonstrate the multi-agent system handling real student queries with autonomous tool usage and intelligent routing.

#### Example 1: Program Search with RAG
![AI Program Query](Visual%20Examples/ai-program-query-demo.png)
*Student asks about "artificial intelligence" programs. The system autonomously invokes the `search_catalog` tool and retrieves detailed program information from the 1000+ page catalog, including course requirements and credit information.*

#### Example 2: System Capabilities
![Core Functions](Visual%20Examples/system-core-functions.png)
*The agent explains its core functions, demonstrating self-awareness of its capabilities including multi-agent coordination, personalized recommendations, and comprehensive student support.*

#### Example 3: Multi-Tool Coordination
![Medical Programs Query](Visual%20Examples/medical-programs-tool-usage.png)
*When asked about medical programs, the system autonomously chains multiple tools: `search_catalog` → `semantic_catalog_search` → `rag_bates`, demonstrating intelligent multi-step task execution without explicit user prompts for each step.*

#### Example 4: Financial Aid Routing
![Financial Aid Response](Visual%20Examples/financial-aid-response.png)
*Query about financial aid automatically routes to the FinancialAidAgent, which uses the `rag_bates` tool to extract specific eligibility requirements and aid types from the catalog. Notice the autonomous tool invocation (shown in the left panel).*

### Key Agent Behaviors Demonstrated

These screenshots illustrate the autonomous agent characteristics:

**🤖 Autonomous Decision-Making:**
- System decides which tools to invoke without being told
- Automatically routes queries to appropriate specialist agents
- Chains multiple tools together for complex queries

**🔧 Tool Use:**
- `search_catalog` - Basic keyword search
- `semantic_catalog_search` - AI-powered semantic search
- `rag_bates` - Retrieval-Augmented Generation over catalog

**🎯 Goal-Oriented Behavior:**
- Pursues the goal of answering student questions completely
- Gathers all relevant information from catalog
- Provides comprehensive, multi-faceted responses

**🧠 Multi-Agent Coordination:**
- Routes admissions questions to AdmissionsAgent
- Routes financial aid questions to FinancialAidAgent
- Routes academic questions to AcademicsAgent

---

**Built for:** [Google & Kaggle 5-Day AI Agents Intensive Course capstone project]

---

## ✨ Key Features

### 🤖 Multi-Agent Architecture
- **Root Orchestrator Agent**: Intelligent query routing and system coordination
- **Specialized Domain Agents**:
  - **AdmissionsAgent**: Handles admission requirements, applications, and enrollment
  - **AcademicsAgent**: Manages programs, courses, and curriculum information  
  - **FinancialAidAgent**: Provides financial aid, scholarships, and cost guidance
- **Sequential Processing**: Complex queries routed to multiple specialists for comprehensive responses

### 🛠️ Enhanced Capabilities
- **MCP Integration**: Model Context Protocol for structured tool management
- **RAG Implementation**: Retrieval Augmented Generation with institutional knowledge base
- **Session Management**: Persistent conversation context and memory
- **Advanced Tools Suite**:
  - Enhanced catalog search with PDF processing
  - Student pathway analysis and recommendations
  - Course scheduling assistance
  - Real-time web information retrieval

### 📊 Observability & Performance
- Comprehensive logging and metrics tracking
- Session state management
- Performance monitoring and optimization
- Error handling and recovery mechanisms

---

## 🏗️ Architecture

```
                    Root Orchestrator Agent
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   Admissions          Academics        Financial Aid
     Agent              Agent               Agent
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                    Enhanced Tools
                           │
                  Session & Memory
                           │
                   Observability
```

---

## 📁 Project Structure

```
student-advisor-capstone-adk/
├── bates_agent/                    # Core agent package
│   ├── agent.py                   # Main agent implementation
│   ├── tools/                     # Enhanced tools suite
│   │   ├── enhanced_tools.py     # Advanced search and analysis
│   │   ├── specialized_agents.py # Multi-agent implementations
│   │   ├── session_memory.py     # Session state management
│   │   ├── observability.py      # Logging and metrics
│   │   └── rag_loader.py         # Document processing for RAG
│   └── data/                     # Agent-specific data storage
├── data/                         # Project data and documents
├── logs/                         # Application logging output
├── main.py                       # Application entry point
├── requirements.txt              # Core project dependencies
├── vector_requirements.txt       # Vector database dependencies
├── ENHANCED_FEATURES.md          # Detailed feature documentation
└── VECTOR_DATABASE_GUIDE.md      # Vector database setup guide
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Google API Key (for Gemini)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/GCB-89/student-advisor-capstone-adk.git
cd student-advisor-capstone-adk

# 2. Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Mac/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Install vector database features
pip install -r vector_requirements.txt
```

### Configuration

Create `bates_agent/.env` with your API key:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

Get your API key at: https://aistudio.google.com/app/apikey

### Launch

```bash
python main.py
```

Access the web interface at: **http://127.0.0.1:8000**

---

## 💬 Usage Examples

### Basic Queries
```
Student: "What are the requirements for the nursing program?"
→ Routes to: AdmissionsAgent + AcademicsAgent

Student: "How much does the welding program cost?"
→ Routes to: FinancialAidAgent

Student: "Help me plan my schedule for next quarter"
→ Uses: schedule_assistance tool via AcademicsAgent
```

### Multi-Agent Coordination
```python
from bates_agent import root_agent

# Complex query gets routed to multiple specialists
response = await root_agent(
    "I need admission requirements and financial aid for computer science"
)

---

## 📚 Documentation

- **[ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)** - Complete system architecture and capabilities
- **[VECTOR_DATABASE_GUIDE.md](VECTOR_DATABASE_GUIDE.md)** - Optional ChromaDB integration guide

---

## 📋 Dependencies

### Core Requirements
- **pypdf>=4.0.0**: PDF document processing
- **google-adk>=2.0.0**: Google Agent Development Kit
- **python-dotenv>=1.0.0**: Environment variable management
- **requests>=2.31.0**: HTTP client for external APIs

### Vector Database (Optional)
See `vector_requirements.txt` for enhanced semantic search capabilities.

---

## 🎓 Capstone Project Context

This project demonstrates **4 core concepts** from the AI Agents Intensive Course:

| Concept | Implementation |
|---------|----------------|
| **Multi-Agent System** | Root orchestrator + 3 specialized agents |
| **Tool Integration (MCP)** | Custom tools for search, analysis, scheduling |
| **Memory & Context** | Session management with persistent profiles |
| **Observability** | Production-ready logging, tracing, metrics |

### Skills Demonstrated
- ✅ AI agent architecture and multi-agent coordination
- ✅ Google ADK integration and cloud services
- ✅ RAG implementation with custom knowledge bases
- ✅ Production software development practices
- ✅ Professional testing and documentation

---

## 👤 About the Developers

- 🔗 **LinkedIn**: [Connect with me](https://www.linkedin.com/in/cepeda-b-41b239331)
- 📊 **Kaggle**: [View my projects](https://www.kaggle.com/cepedabraxton)
- 💻 **GitHub**: [@GCB-89](https://github.com/GCB-89)

- 💻 **GitHub**: [@xiexinchun25](https://github.com/xiexinchun25)
- 📊 **Kaggle**: [View my projects](https://www.kaggle.com/nellykwan)

Data Science student specializing in AI/ML, with focus on agentic systems, RAG, and MLOps.

---

## 🙏 Acknowledgments

- Built for the [Google & Kaggle 5-Day AI Agents Intensive Course](https://rsvp.withgoogle.com/events/google-ai-agents-intensive_2025)
- Powered by [Google's Agent Development Kit](https://github.com/google/genkit)
- Data from Bates Technical College 2025-26 Catalog

---

⭐ **If you find this project helpful, please give it a star!**

*Capstone Project - AI Agents Intensive - November 2025*
