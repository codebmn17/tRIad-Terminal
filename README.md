# Triad Terminal — Multi-Assistant Command Center

🚀 **Enhanced terminal with comprehensive multi-assistant coordination, Storm integration, SQLite history persistence, and dataset catalog functionality.**

## 🌟 Features

### Multi-Assistant Command Center
- **Session Management**: Create and manage multi-assistant chat sessions
- **Group Chat**: Coordinate multiple AI assistants in real-time conversations  
- **Agent Discovery**: Automatic discovery and registration of available assistant types
- **Role-based Coordination**: Specialized agents (Planner, Critic, Executor, Chat)

### Storm Integration
- **WebSocket Communication**: Real-time agent-to-agent communication
- **Distributed Task Orchestration**: Submit and monitor distributed tasks across agents
- **Load Balancing**: Automatic task assignment based on agent capabilities and load
- **Coordination Sessions**: Create multi-agent collaboration sessions

### SQLite History Persistence  
- **Comprehensive Tracking**: Chat messages, commands, assistant interactions
- **Session Analytics**: Detailed statistics and usage patterns
- **Multi-Assistant History**: Complete conversation history across all sessions
- **Automatic Cleanup**: Configurable retention policies

### Dataset Catalog
- **Auto-Analysis**: Automatic schema detection for CSV, JSON, Parquet files
- **Usage Tracking**: Monitor dataset access patterns and statistics
- **Search & Discovery**: Tag-based search and metadata indexing
- **File Management**: Upload, register, and manage datasets

### Enhanced API (v2)
- **RESTful Endpoints**: Comprehensive API for all functionality
- **Interactive Documentation**: Built-in Swagger/OpenAPI docs
- **Async Operations**: Full async/await support throughout
- **Type Safety**: Pydantic models for request/response validation

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (3.12 recommended)
- SQLite 3.8+ (included with Python)

### Installation

```bash
# Clone the repository
git clone https://github.com/codebmn17/tRIad-Terminal.git
cd tRIad-Terminal

# Install dependencies
pip install -r requirements.txt

# Install enhanced dependencies for multi-assistant features
pip install aiosqlite sqlalchemy alembic websockets redis pandas pyarrow aiofiles rich typer jinja2 python-multipart
```

### Start the Multi-Assistant Command Center

```bash
# Start the enhanced API server
python -c "from api.main import run_server; run_server()"

# The server starts on http://127.0.0.1:8000
# - API Documentation: http://127.0.0.1:8000/docs
# - Storm WebSocket: ws://localhost:8765
```

### Basic Usage

#### 1. Create a Multi-Assistant Session

```bash
curl -X POST "http://127.0.0.1:8000/api/v2/multi-assistant/sessions" \
     -H "Content-Type: application/json" \
     -d '{
       "session_name": "Planning Session",
       "assistant_types": ["PlannerAgent", "CriticAgent", "ExecutorAgent"],
       "initial_message": "Help me plan a software project"
     }'
```

#### 2. Send Messages to Group Chat

```bash
curl -X POST "http://127.0.0.1:8000/api/v2/multi-assistant/sessions/{session_id}/messages" \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "your-session-id",
       "message": "What are the key steps for project planning?",
       "sender": "user"
     }'
```

#### 3. Upload and Catalog Datasets

```bash
curl -X POST "http://127.0.0.1:8000/api/v2/datasets/upload" \
     -F "file=@your_dataset.csv" \
     -F "dataset_id=sample_data" \
     -F "name=Sample Dataset" \
     -F "description=Example dataset for analysis"
```

#### 4. Submit Distributed Tasks

```bash
curl -X POST "http://127.0.0.1:8000/api/v2/storm/tasks" \
     -H "Content-Type: application/json" \
     -d '{
       "task_type": "analysis",
       "description": "Analyze dataset patterns",
       "payload": {"dataset_id": "sample_data"},
       "required_capabilities": ["data_analysis"]
     }'
```

## 🏗️ Architecture

### Service Layer
```
triad/services/
├── history_persistence.py    # SQLite-based history tracking
├── dataset_catalog.py        # Dataset management and analysis
└── storm_integration.py      # Distributed agent coordination
```

### API Layer (v2)
```
api/routers/v2/
├── multi_assistant.py        # Session and group chat management
├── history.py               # History access and analytics
├── dataset_catalog.py       # Dataset CRUD operations
└── storm.py                 # Task orchestration and messaging
```

### Agent System
```
triad/agents/
├── core.py                  # Base agent framework
├── registry.py              # Agent discovery and registration
├── rooms.py                 # Multi-agent communication rooms
└── builtins/                # Built-in agent implementations
    ├── planner.py           # Task planning agent
    ├── critic.py            # Review and critique agent
    └── executor.py          # Action execution agent
```

## 📊 API Endpoints

### Multi-Assistant Management
- `POST /api/v2/multi-assistant/sessions` - Create session
- `GET /api/v2/multi-assistant/sessions/{id}` - Get session info
- `POST /api/v2/multi-assistant/sessions/{id}/messages` - Send message
- `GET /api/v2/multi-assistant/available-assistants` - List assistants

### History & Analytics  
- `GET /api/v2/history/chat` - Chat message history
- `GET /api/v2/history/commands` - Command execution history
- `GET /api/v2/history/interactions` - Assistant interaction history
- `GET /api/v2/history/stats` - Overall statistics

### Dataset Catalog
- `POST /api/v2/datasets/upload` - Upload dataset
- `GET /api/v2/datasets` - List datasets
- `GET /api/v2/datasets/search` - Search datasets
- `POST /api/v2/datasets/{id}/usage` - Log usage

### Storm Integration
- `POST /api/v2/storm/tasks` - Submit task
- `GET /api/v2/storm/tasks/{id}` - Get task status
- `GET /api/v2/storm/agents` - List connected agents
- `POST /api/v2/storm/coordination` - Create coordination session

## ⚙️ Configuration

Create a `.env` file or set environment variables:

```env
# Database Settings
TRIAD_DB_PATH=~/.triad/history.db
DATASET_CATALOG_PATH=~/.triad/datasets

# Storm Integration
STORM_WEBSOCKET_PORT=8765
STORM_COORDINATION_TIMEOUT=30.0

# API Settings  
API_HOST=127.0.0.1
API_PORT=8000
API_DEBUG=true

# Feature Flags
ENABLE_STORM_INTEGRATION=true
ENABLE_DATASET_CATALOG=true
ENABLE_HISTORY_PERSISTENCE=true
ENABLE_MULTI_ASSISTANT=true
```

## 🎯 Implemented Features

### ✅ Phase 1: Core Infrastructure (COMPLETED)
- [x] **Multi-assistant session management** - Create and manage sessions with multiple AI assistants
- [x] **Storm integration with WebSocket communication** - Real-time agent coordination at ws://localhost:8765
- [x] **SQLite history persistence** - Comprehensive tracking of all interactions
- [x] **Dataset catalog with auto-analysis** - Upload, analyze, and manage datasets
- [x] **Enhanced API v2 endpoints** - Complete RESTful API with documentation

### 🔧 Development

### Project Structure
```
tRIad-Terminal/
├── api/                     # FastAPI application
│   ├── main.py             # Enhanced app with v2 endpoints
│   └── routers/v2/         # v2 API routers
├── triad/                  # Core framework
│   ├── services/           # Business logic services
│   └── agents/             # Agent system
├── config/                 # Configuration management
├── tests/                  # Test suite
└── docs/                   # Documentation
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
python -m pytest tests/ -v
```

### Adding Custom Agents
```python
from triad.agents.core import Agent, Message, Role

class CustomAgent(Agent):
    def __init__(self):
        super().__init__("custom-agent", role=Role("specialist", icon="⭐"))
    
    async def handle(self, msg: Message) -> None:
        if msg.sender == self.name:
            return
        # Custom logic here
        await self.say(msg.room, f"Custom response to: {msg.content}")

# Register the agent
from triad.agents.registry import register_agent
register_agent("CustomAgent", CustomAgent)
```

## 📈 Live Demonstration

The multi-assistant command center is **currently running** and can be tested:

```bash
# Test available assistants
curl http://127.0.0.1:8000/api/v2/multi-assistant/available-assistants

# Check Storm integration status  
curl http://127.0.0.1:8000/api/v2/storm/status

# View API documentation
open http://127.0.0.1:8000/docs
```

**Available Assistants:**
- PlannerAgent: Task planning and breakdown
- CriticAgent: Review and critique functionality  
- ExecutorAgent: Action execution coordination
- ChatAgent: General conversation assistance

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes**: Follow existing code patterns
4. **Add tests**: Ensure comprehensive test coverage
5. **Submit PR**: Include detailed description

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ using Python, FastAPI, SQLite, and WebSockets**