# Marketing Multi-Agent System Analysis

This project analyzes a synthetic dataset for an AI/ML assessment focused on a **3-agent marketing system** covering Lead Triage, Engagement, and Campaign Optimization.

## 🎯 Project Overview

### Assessment Context
This appears to be an AI/ML engineering assessment involving:
- **Multi-agent system analysis** with 3 specialized agents
- **Synthetic marketing data** spanning 4 months (May-August 2025)
- **Memory system evaluation** (short-term, long-term, episodic, semantic)
- **MCP (Model Context Protocol) transport analysis**
- **Agent handoff and escalation protocols**

### Agents in the System
1. **Lead Triage Agent**: Categorizes and scores incoming leads
2. **Engagement Agent**: Handles lead interactions and outreach
3. **Campaign Optimization Agent**: Optimizes campaign performance

## 📊 Dataset Components

### Core Business Data
- **campaigns.csv**: Campaign metadata, budgets, objectives
- **leads.csv**: Lead records with triage scores and status
- **interactions.csv**: Event-level engagement logs
- **conversions.csv**: Conversion outcomes and values
- **agent_actions.csv**: Agent handoffs, escalations, and actions

### Memory Systems
- **memory_short_term.csv**: Ephemeral conversation context
- **memory_long_term.csv**: Persistent lead preferences
- **memory_episodic.csv**: Successful playbooks and outcomes
- **semantic_kg_triples.csv**: Domain knowledge graph

### Transport & Infrastructure
- **mcp_jsonrpc_calls.csv**: JSON-RPC call logs
- **transport_websocket_sessions.csv**: WebSocket metrics
- **transport_http_requests.csv**: HTTP request metrics
- **security_auth_events.csv**: Authentication events

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Virtual environment support

### Installation

1. **Clone/Navigate to the project directory**
   ```bash
   cd /Users/srijanratrey/Documents/Learning\ and\ coding/Assign
   ```

2. **Activate the virtual environment**
   ```bash
   source marketing_analysis_env/bin/activate
   ```

3. **Install dependencies** (already done in setup)
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch Jupyter**
   ```bash
   jupyter lab
   ```

5. **Open the main analysis notebook**
   ```
   notebooks/marketing_analysis.ipynb
   ```

## 📁 Project Structure

```
├── marketing_analysis_env/          # Virtual environment
├── marketing_multi_agent_dataset_v1_final/  # Source dataset
├── agents/                          # Multi-agent system implementation
│   ├── __init__.py
│   ├── base_agent.py               # Base agent framework
│   └── lead_triage_agent.py        # Lead triage agent implementation
├── mcp_server/                      # Model Context Protocol server
│   └── server.py                   # MCP server with JSON-RPC 2.0
├── memory_systems/                  # Adaptive memory architecture
│   └── memory_manager.py           # 4-tier memory management
├── api/                            # API models and schemas
│   └── models.py                   # Pydantic models for validation
├── notebooks/                      # Analysis notebooks
│   └── marketing_analysis.ipynb   # Main analysis notebook
├── docs/                           # Documentation
│   └── adrs/                       # Architecture Decision Records
│       ├── 001-multi-agent-architecture.md
│       └── 002-memory-system-design.md
├── scripts/                        # Utility scripts
│   └── setup_verification.py      # Setup verification
├── PROJECT_PLAN.md                 # Comprehensive project plan
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🔍 Key Analysis Areas

### 1. Lead Triage Analysis
- Lead classification by triage category
- Lead scoring distribution and effectiveness
- Lead status progression analysis

### 2. Agent Performance Evaluation
- Agent action patterns and frequency
- Handoff protocols between agents
- Escalation triggers and success rates

### 3. Campaign Optimization
- A/B testing analysis of creative variants
- Campaign ROI and performance metrics
- Attribution modeling for conversions

### 4. Memory System Assessment
- Memory consolidation patterns
- Knowledge graph relationship analysis
- Context retention effectiveness

### 5. MCP Transport Analysis
- System reliability and latency metrics
- Authentication and security patterns
- Resource access optimization

## 📈 Potential Machine Learning Applications

### Classification Tasks
- **Lead Triage Classification**: Predict optimal triage category
- **Conversion Prediction**: Identify high-value leads
- **Escalation Prediction**: Anticipate when human intervention needed

### Optimization Tasks
- **Campaign Budget Allocation**: Optimize spend across channels
- **A/B Test Design**: Automated variant generation
- **Agent Workload Balancing**: Distribute leads optimally

### Sequence Analysis
- **Lead Journey Mapping**: Trace lead progression paths
- **Agent Handoff Optimization**: Improve transition protocols
- **Memory Consolidation**: Optimize knowledge retention

## 🛠 Available Tools and Libraries

### Data Science Stack
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **scipy**: Statistical analysis
- **statsmodels**: Advanced statistical modeling

### Machine Learning
- **scikit-learn**: General ML algorithms
- **xgboost**: Gradient boosting
- **lightgbm**: Fast gradient boosting

### Visualization
- **matplotlib**: Static plotting
- **seaborn**: Statistical visualization
- **plotly**: Interactive plots and dashboards

### Specialized
- **networkx**: Knowledge graph analysis
- **nltk/textblob**: Text processing for interactions
- **dash**: Interactive dashboard creation

## 📋 Next Steps

1. **Data Exploration**: Run the main analysis notebook
2. **Feature Engineering**: Create domain-specific features
3. **Model Development**: Build predictive models for key use cases
4. **Dashboard Creation**: Build interactive monitoring dashboard
5. **Performance Analysis**: Evaluate agent and system performance
6. **Recommendations**: Provide optimization suggestions

## 🔧 Utilities

### Multi-Agent System
```python
from agents.lead_triage_agent import LeadTriageAgent
from mcp_server.server import MCPServer
from memory_systems.memory_manager import MemoryManager

# Initialize memory manager
memory_manager = MemoryManager()
await memory_manager.initialize()

# Start MCP server
server = MCPServer()
await server.start_server()
```

### Data Analysis
```python
# Use the Jupyter notebook for comprehensive data analysis
# notebooks/marketing_analysis.ipynb contains the full analysis pipeline
```

## 📝 Assessment Suggestions

Based on the dataset structure, this assessment likely evaluates:

1. **Data Analysis Skills**: Ability to explore and understand complex multi-agent data
2. **ML Engineering**: Building robust pipelines for agent performance optimization
3. **System Design**: Understanding of multi-agent architectures and protocols
4. **Business Acumen**: Translating technical findings into marketing insights
5. **Communication**: Clear presentation of findings and recommendations

## 🎯 Success Criteria

To excel in this assessment, focus on:
- **Comprehensive data exploration** with meaningful insights
- **Robust feature engineering** specific to marketing use cases
- **Practical ML models** that solve real business problems
- **Clear visualization** of agent interactions and performance
- **Actionable recommendations** for system optimization

---

*This project demonstrates AI/ML engineering capabilities in the context of marketing automation and multi-agent systems.*
