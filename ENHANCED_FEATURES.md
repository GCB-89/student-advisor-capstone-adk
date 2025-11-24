# 🎓 Enhanced Bates Agent - Multi-Agent System Documentation

## 🚀 **Key Features Implemented**

### 1. 🤝 **Multi-Agent System (Sequential Agents)**
- **Root Orchestrator Agent**: Coordinates the entire system and routes queries
- **Specialized Agents**:
  - **AdmissionsAgent**: Handles admission requirements, applications, enrollment
  - **AcademicsAgent**: Manages programs, courses, curriculum information  
  - **FinancialAidAgent**: Provides financial aid, scholarship, and cost information
- **Sequential Processing**: Queries are routed to appropriate specialists, with complex queries getting multiple perspectives
- **Intelligent Routing**: Automatic query analysis determines which specialist(s) should handle each request

### 2. 🛠️ **Enhanced Tools Integration**
- **MCP (Model Context Protocol) Integration**: Structured tool management and execution
- **Custom Enhanced Tools**:
  - `enhanced_catalog_search`: Advanced PDF search with multiple strategies
  - `student_pathway_analysis`: AI-powered educational pathway recommendations
  - `schedule_assistance`: Course scheduling and planning support
  - `bates_website_search`: External information retrieval
- **Google Search Integration**: (Framework ready for API integration)
- **OpenAPI Tools**: Extensible architecture for external service integration

### 3. 🧠 **Sessions & Memory System**
- **InMemorySessionService**: Google ADK session management
- **Long-term Memory (BatesMemoryBank)**:
  - Student profile persistence
  - Interaction history tracking
  - Interest and preference learning
  - Recommendation tracking
- **Context Compaction**: Intelligent summary generation for agent context
- **Session State Management**: Active session tracking with automatic cleanup

### 4. 📊 **Comprehensive Observability**
- **Advanced Logging System**:
  - Multi-level logging (DEBUG, INFO, WARNING, ERROR)
  - Separate log files for different concerns
  - Structured logging with context information
- **Distributed Tracing**:
  - Operation tracking across agent interactions
  - Performance measurement and bottleneck identification
  - Trace export capabilities for analysis
- **Metrics Collection**:
  - Counters: Query routing, agent usage, error rates
  - Timers: Response times, operation durations
  - Gauges: Active sessions, system health indicators
- **Performance Monitoring**: Automated performance tracking with decorators

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────┐
│                Root Orchestrator Agent                  │
│         (Multi-Agent Query Coordination)               │
└─────────────┬───────────────┬───────────────┬───────────┘
              │               │               │
    ┌─────────▼────────┐ ┌───▼────────┐ ┌────▼──────────┐
    │ AdmissionsAgent  │ │ Academics  │ │ FinancialAid  │
    │                  │ │   Agent    │ │    Agent      │
    └──────────────────┘ └────────────┘ └───────────────┘
              │               │               │
    ┌─────────▼───────────────▼───────────────▼───────────┐
    │              Enhanced Tools Suite                   │
    │  • Catalog Search  • Pathway Analysis              │
    │  • Schedule Help   • Web Search                     │
    └─────────────────────────────────────────────────────┘
              │
    ┌─────────▼───────────────────────────────────────────┐
    │           Session & Memory Management               │
    │  • Student Profiles  • Interaction History         │
    │  • Context Compaction • Long-term Learning         │
    └─────────────────────────────────────────────────────┘
              │
    ┌─────────▼───────────────────────────────────────────┐
    │              Observability Layer                    │
    │  • Logging  • Tracing  • Metrics  • Monitoring     │
    └─────────────────────────────────────────────────────┘
```

## 🎯 **Usage Examples**

### Multi-Agent Query Processing
```python
from bates_agent import root_agent

# Complex query gets routed to multiple specialists
response = root_agent.run(
    "I'm interested in the nursing program. What are the requirements and costs?"
)
# Routes to: AdmissionsAgent + AcademicsAgent + FinancialAidAgent
```

### Session Management
```python
from bates_agent.tools.session_memory import session_manager

# Create persistent session
session_id = session_manager.create_session("student123")

# Queries automatically use student context
session_manager.record_interaction(
    session_id, "program_inquiry", "nursing program", "detailed_info_provided"
)
```

### Observability
```python
from bates_agent.tools.observability import get_metrics, get_tracer

# Get system performance metrics
metrics = get_metrics().get_metrics()
print(f"Total queries: {metrics['counters']['queries_processed']}")

# Get recent traces for debugging
tracer = get_tracer()
recent_traces = tracer.get_traces(limit=5)
```

## 📁 **File Structure**
```
bates_agent/
├── agent.py                    # Enhanced root orchestrator agent
├── __init__.py                 # Package initialization
├── data/
│   └── BatesTech2025-26Catalog.pdf
├── tools/
│   ├── __init__.py
│   ├── rag_loader.py           # Original RAG functionality
│   ├── specialized_agents.py   # Domain-specific agents
│   ├── enhanced_tools.py       # Advanced tool suite
│   ├── session_memory.py       # Memory & session management
│   └── observability.py        # Logging, tracing, metrics
├── logs/                       # Auto-generated log files
└── data/
    └── memory_bank/            # Persistent student data
```

## 🚦 **Getting Started**

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch Web Interface**:
   ```bash
   python main.py
   ```

3. **Access at**: `http://127.0.0.1:8000`

## 📈 **Key Metrics & KPIs**

- **Query Routing Accuracy**: Automatic classification into specialist domains
- **Response Time**: End-to-end query processing performance
- **Student Retention**: Session continuation and re-engagement rates
- **Agent Utilization**: Distribution of queries across specialists
- **Memory Effectiveness**: Context relevance in follow-up interactions

## 🔧 **Configuration Options**

- **Logging Levels**: Configurable verbosity (DEBUG through CRITICAL)
- **Memory Retention**: Adjustable history limits and cleanup intervals
- **Session Timeouts**: Configurable session expiration policies
- **Agent Routing**: Customizable keyword-based routing logic
- **Performance Monitoring**: Selective instrumentation of operations

## 🎉 **Advanced Capabilities**

✅ **Intelligent Query Routing**: Automatic domain detection and agent selection  
✅ **Multi-Perspective Responses**: Complex queries get insights from multiple specialists  
✅ **Student Learning**: System learns from interactions to improve recommendations  
✅ **Performance Optimization**: Real-time monitoring and bottleneck identification  
✅ **Scalable Architecture**: Easy addition of new specialist agents and tools  
✅ **Rich Context Awareness**: Persistent student profiles with interaction history  
✅ **Comprehensive Monitoring**: Full observability into system operations  

