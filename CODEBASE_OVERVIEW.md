# AI MCP Toolkit - Analytical Codebase Overview

**Version:** 0.3.0  
**Last Updated:** 2025-01-03  
**Status:** Production-Ready with Active Development

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Architecture](#project-architecture)
3. [Technology Stack](#technology-stack)
4. [Core Components](#core-components)
5. [Directory Structure](#directory-structure)
6. [Key Features & Agents](#key-features--agents)
7. [Database Schema](#database-schema)
8. [API Endpoints](#api-endpoints)
9. [Frontend Architecture](#frontend-architecture)
10. [Development Workflow](#development-workflow)
11. [Deployment Configuration](#deployment-configuration)
12. [Current Implementation Status](#current-implementation-status)
13. [Quick Reference Index](#quick-reference-index)

---

## Executive Summary

**AI MCP Toolkit** is a comprehensive text processing system built on the Model Context Protocol (MCP) standard. It provides a production-ready platform for AI-powered text analysis, processing, and manipulation using local AI models via Ollama.

### Key Highlights

- ✅ **8+ AI Agents**: Specialized text processing tools (cleaner, analyzer, summarizer, grammar checker, etc.)
- ✅ **MCP Protocol Compliant**: Full implementation of MCP standard for AI applications
- ✅ **Modern Web UI**: ChatGPT-like interface built with SvelteKit
- ✅ **Production Infrastructure**: MongoDB Atlas, Redis caching, GPU acceleration
- ✅ **Cross-Platform**: Supports Linux (NVIDIA GPU), macOS (Apple Silicon), Windows
- ✅ **Security**: Authentication, authorization, per-user data isolation
- ✅ **Local File Storage**: Dual storage (MongoDB metadata + local filesystem)

### Current Status

- **Phase 1 (Core MCP)**: 25% complete (Resource Management ✅, Prompt System ⏳, Messages ⏳)
- **Phase 2 (Agent Cooperation)**: 0% (planned)
- **Phase 3 (Advanced Features)**: 64% complete (Security ✅, Per-User Storage ✅, File Storage ✅)
- **Phase 0 (Compound Search)**: 80% complete (in progress)

---

## Project Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser (Client)                     │
│              SvelteKit Frontend (Port 5173)                  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST (API Proxy)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              SvelteKit API Routes (/api/*)                   │
│              - Pure HTTP proxies to backend                 │
│              - Session cookie forwarding                    │
│              - NO business logic                            │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            FastAPI Backend Server (Port 8000)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MCP Protocol Implementation                         │   │
│  │  - Resource Management                               │   │
│  │  - Tool Execution                                    │   │
│  │  - Prompt Templates                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  AI Agents (11 agents)                               │   │
│  │  - Text Cleaner, Analyzer, Summarizer                │   │
│  │  - Grammar Checker, Language Detector                │   │
│  │  - Sentiment Analyzer, Anonymizer                    │   │
│  │  - PDF Extractor, Image OCR                          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Managers & Services                                 │   │
│  │  - ResourceManager, ConversationManager               │   │
│  │  - IngestionService, SearchService                   │   │
│  │  - FileStorageService, EmbeddingService              │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────┬───────────────────────────────┬─────────────────┘
             │                               │
             ▼                               ▼
┌────────────────────────┐    ┌────────────────────────┐
│   MongoDB Atlas        │    │   Redis Cache          │
│   - Users, Sessions    │    │   - Session storage    │
│   - Resources, Chunks  │    │   - Search suggestions │
│   - Conversations      │    │   - Caching            │
└────────────────────────┘    └────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│      Ollama (Local AI Models)          │
│      Port 11434                        │
│      - llama3.1:8b, qwen2.5:14b        │
│      - nomic-embed-text (embeddings)    │
│      - llava (vision)                  │
└────────────────────────────────────────┘
```

### Architecture Principles

1. **Frontend-Backend Separation**: Frontend (SvelteKit) ALWAYS uses backend API, never direct database access
2. **MCP Protocol First**: All agents expose MCP-compliant tools and resources
3. **Async Throughout**: All I/O operations are async (Motor, aiohttp, FastAPI)
4. **Per-User Isolation**: All data is scoped by user_id with proper authentication
5. **Dual Storage**: MongoDB for metadata/structured data, local filesystem for binary files

---

## Technology Stack

### Backend (Python 3.11+)

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Framework** | FastAPI | 0.104.0+ | Web API framework |
| **Server** | Uvicorn | 0.24.0+ | ASGI server |
| **MCP** | mcp | 1.0.0+ | MCP protocol implementation |
| **Database** | Motor | 3.3.0+ | Async MongoDB driver |
| **ODM** | Beanie | 1.23.0+ | MongoDB ODM |
| **Cache** | Redis | 4.5.0+ | Caching and session storage |
| **AI/ML** | Ollama | 0.3.0+ | Local AI models |
| **NLP** | spaCy, NLTK | Latest | Text processing |
| **Embeddings** | sentence-transformers | 2.2.0+ | Vector embeddings |
| **OCR** | pytesseract | 0.3.10+ | Image text extraction |
| **Validation** | Pydantic | 2.5.0+ | Data validation |
| **HTTP** | aiohttp | 3.8.0+ | Async HTTP client |
| **Files** | aiofiles | 23.2.0+ | Async file operations |

### Frontend (TypeScript/JavaScript)

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Framework** | SvelteKit | Latest | Full-stack framework |
| **Language** | TypeScript | 5.0.0+ | Type safety |
| **Styling** | Tailwind CSS | 3.3.0+ | Utility-first CSS |
| **Icons** | Lucide Svelte | Latest | Icon library |
| **HTTP** | Fetch API | Built-in | API calls |

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Database** | MongoDB Atlas | Cloud MongoDB cluster |
| **Cache** | Redis | Session storage, caching |
| **Containerization** | Docker + Docker Compose | Development/production |
| **Reverse Proxy** | NGINX | Production deployment |
| **AI Models** | Ollama | Local LLM inference |

---

## Core Components

### 1. MCP Server (`server/mcp_server.py`)

**Purpose**: Main MCP protocol implementation

**Key Responsibilities**:
- Register MCP protocol handlers (tools, resources, prompts)
- Initialize and manage AI agents
- Coordinate database connections
- Handle MCP protocol requests

**Key Methods**:
- `_register_handlers()`: Register MCP handlers
- `_initialize_agents()`: Initialize all AI agents
- `list_resources()`: List available resources
- `read_resource()`: Read specific resource
- `call_tool()`: Execute agent tools

### 2. AI Agents (`agents/`)

**Base Class**: `BaseAgent` (`agents/base_agent.py`)

**All agents inherit from BaseAgent and implement**:
- `get_tools()`: Return MCP Tool definitions
- `execute_tool()`: Execute tool with arguments
- `validate_text_input()`: Input validation
- `chunk_text()`: Text chunking for large inputs

**Available Agents** (11 total):

1. **TextCleanerAgent** - Remove special characters, normalize text
2. **DiacriticRemoverAgent** - Remove accents and diacritical marks
3. **TextAnalyzerAgent** - Comprehensive text statistics
4. **GrammarCheckerAgent** - Fix grammar and spelling
5. **TextSummarizerAgent** - Generate summaries
6. **LanguageDetectorAgent** - Detect text language
7. **SentimentAnalyzerAgent** - Analyze emotional tone
8. **TextAnonymizerAgent** - Anonymize personal information
9. **PDFExtractorAgent** - Extract text from PDF files
10. **ImageOCRAgent** - OCR and image description

### 3. Managers (`managers/`)

**ResourceManager** (`managers/resource_manager.py`):
- CRUD operations for MCP resources
- MongoDB storage and retrieval
- Resource search and filtering

**ConversationManager** (`managers/conversation_manager.py`):
- Per-user conversation management
- Message storage and retrieval
- Conversation CRUD operations

**UserManager** (`managers/user_manager.py`):
- User registration and authentication
- Password hashing (bcrypt)
- User profile management

**SessionManager** (`managers/session_manager.py`):
- Session creation and validation
- HTTP-only cookie management
- Session expiration (24h)

**PromptManager** (`managers/prompt_manager.py`):
- Prompt template storage and retrieval
- Template rendering with variables

**EmbeddingManager** (`managers/embedding_manager.py`):
- Vector embedding generation
- Embedding storage and retrieval

### 4. Services (`services/`)

**IngestionService** (`services/ingestion_service.py`):
- Document upload and processing
- Text extraction (PDF, images, CSV)
- Chunking and embedding generation
- Metadata extraction

**SearchService** (`services/search_service.py`):
- Compound search (keyword + semantic + hybrid)
- MongoDB Atlas vector search
- Result scoring and ranking

**FileStorageService** (`services/file_storage_service.py`):
- Local file storage (UUID-based organization)
- User-isolated file access
- File metadata management

**ImageCaptionService** (`services/image_caption_service.py`):
- Image captioning (LLaVA/Moondream)
- OCR text extraction (Tesseract)
- Embedding generation for images

**EmbeddingService** (`services/embedding_service.py`):
- Text embedding generation (nomic-embed-text)
- Vector search support

**SuggestionService** (`services/suggestion_service.py`):
- Redis-based search suggestions
- Term indexing and prefix matching

**MetadataExtractor** (`services/metadata_extractor.py`):
- Keyword extraction (IDs, emails, IBANs)
- Vendor/company name detection
- Currency and amount extraction

**QueryAnalyzer** (`services/query_analyzer.py`):
- Query pattern detection (money, IDs, dates)
- Search strategy estimation
- Entity extraction

### 5. Database Models (`models/`)

**Document Models** (Beanie ODM):
- `User` - User accounts
- `Session` - User sessions
- `AuditLog` - Security audit trail
- `Resource` - MCP resources
- `ResourceChunk` - Searchable document chunks
- `Conversation` - User conversations
- `Message` - Chat messages
- `Prompt` - Prompt templates
- `SearchCategory` - Dynamic search categories

**Location**: Models defined in `models/database.py` (via imports from `models/documents.py`)

---

## Directory Structure

```
ai-mcp-toolkit/
├── src/ai_mcp_toolkit/          # Python source code
│   ├── agents/                  # AI agents (11 agents)
│   │   ├── base_agent.py        # Base class for all agents
│   │   ├── text_cleaner.py
│   │   ├── text_analyzer.py
│   │   └── ...
│   ├── server/                  # Server implementations
│   │   ├── mcp_server.py        # MCP protocol server
│   │   └── http_server.py       # FastAPI REST API
│   ├── managers/                # Business logic managers
│   │   ├── resource_manager.py
│   │   ├── conversation_manager.py
│   │   ├── user_manager.py
│   │   └── ...
│   ├── services/                # Service layer
│   │   ├── ingestion_service.py
│   │   ├── search_service.py
│   │   ├── file_storage_service.py
│   │   └── ...
│   ├── models/                  # Data models
│   │   ├── documents.py         # Beanie document models
│   │   ├── database.py          # Database connection
│   │   └── ollama_client.py     # Ollama client
│   ├── processors/              # File processors
│   │   ├── pdf_processor.py
│   │   ├── image_processor.py
│   │   └── csv_processor.py
│   └── utils/                   # Utilities
│       ├── config.py            # Configuration management
│       ├── logger.py            # Logging
│       ├── auth.py              # Authentication
│       └── ...
├── ui/                          # SvelteKit frontend
│   ├── src/
│   │   ├── routes/              # SvelteKit routes
│   │   │   ├── chat/            # Chat interface
│   │   │   ├── agents/           # Agent pages
│   │   │   ├── resources/        # Resource management
│   │   │   ├── search/           # Search interface
│   │   │   └── api/              # API proxy routes
│   │   ├── lib/
│   │   │   ├── components/      # Svelte components
│   │   │   ├── services/        # API clients
│   │   │   └── stores/          # State management
│   │   └── hooks.server.js      # Server-side hooks
│   └── package.json
├── docs/                        # Documentation
├── configs/templates/           # Configuration templates
├── pyproject.toml              # Python dependencies
├── docker-compose.yml           # Docker setup
├── config.yaml                  # Configuration file
└── README.md                    # Main documentation
```

---

## Key Features & Agents

### AI Text Processing Agents

| Agent | Tool Name | Purpose | Key Features |
|-------|-----------|---------|--------------|
| **Text Cleaner** | `clean_text` | Remove special characters | Symbol removal, normalization |
| **Diacritic Remover** | `remove_diacritics` | Remove accents | Unicode normalization |
| **Text Analyzer** | `analyze_text` | Text statistics | Word count, readability, sentiment |
| **Grammar Checker** | `check_grammar` | Fix grammar | AI-powered corrections |
| **Text Summarizer** | `summarize_text` | Generate summaries | Customizable length |
| **Language Detector** | `detect_language` | Detect language | Multi-language support |
| **Sentiment Analyzer** | `analyze_sentiment` | Emotional analysis | Positive/negative/neutral |
| **Text Anonymizer** | `anonymize_text` | Anonymize data | PII removal |

### Document Processing

| Feature | Service | Purpose |
|---------|---------|---------|
| **PDF Extraction** | PDFExtractorAgent | Extract text from PDFs |
| **Image OCR** | ImageOCRAgent | OCR + AI description |
| **CSV Processing** | CSVProcessor | Row-level chunking |
| **Text Normalization** | TextNormalizer | Diacritic-insensitive search |

### Search Capabilities

- **Compound Search**: Keyword + semantic + hybrid
- **Vector Search**: MongoDB Atlas vector search
- **Suggestions**: Redis-based prefix matching
- **Category Search**: Dynamic vendor/people/price matching
- **Image Search**: Caption + OCR text search

---

## Database Schema

### MongoDB Collections

**Users** (`users`):
```python
{
    "id": ObjectId,
    "email": str,  # Unique
    "password_hash": str,
    "role": str,  # "USER" | "ADMIN"
    "created_at": datetime,
    "updated_at": datetime
}
```

**Sessions** (`sessions`):
```python
{
    "id": ObjectId,
    "user_id": ObjectId,
    "session_token": str,  # Unique
    "expires_at": datetime,
    "created_at": datetime
}
```

**Resources** (`resources`):
```python
{
    "id": ObjectId,
    "uri": str,  # Unique MCP URI
    "name": str,
    "description": str,
    "mime_type": str,
    "owner_id": ObjectId,
    "company_id": ObjectId,
    "metadata": dict,
    "file_storage": {
        "file_id": str,  # UUID
        "file_path": str,
        "relative_path": str
    },
    "created_at": datetime,
    "updated_at": datetime
}
```

**ResourceChunks** (`resource_chunks`):
```python
{
    "id": ObjectId,
    "resource_id": ObjectId,
    "owner_id": ObjectId,
    "company_id": ObjectId,
    "chunk_type": str,  # "text" | "image" | "csv_row"
    "text": str,
    "text_normalized": str,  # Diacritic-normalized
    "keywords": [str],
    "vendor": str,
    "entities": [str],
    "currency": str,
    "amounts_cents": [int],
    "text_embedding": [float],  # 768-d vector
    "page_number": int,
    "row_index": int,
    "created_at": datetime
}
```

**Conversations** (`conversations`):
```python
{
    "id": ObjectId,
    "user_id": ObjectId,  # Per-user isolation
    "title": str,
    "messages": [
        {
            "role": str,  # "user" | "assistant"
            "content": str,
            "model": str,
            "metrics": {
                "tokens": int,
                "speed": float,  # tokens/second
                "time": float  # seconds
            },
            "timestamp": datetime
        }
    ],
    "created_at": datetime,
    "updated_at": datetime
}
```

**SearchCategories** (`search_categories`):
```python
{
    "id": ObjectId,
    "company_id": ObjectId,
    "category_type": str,  # "vendor" | "people" | "price"
    "name": str,
    "patterns": [str],  # Regex patterns
    "enabled": bool,
    "created_at": datetime
}
```

### Indexes

- **Users**: `email` (unique)
- **Sessions**: `session_token` (unique), `user_id`, `expires_at`
- **Resources**: `uri` (unique), `owner_id`, `company_id`
- **ResourceChunks**: `resource_id`, `owner_id`, `company_id`, `text_embedding` (vector)
- **Conversations**: `user_id`, `created_at`

---

## API Endpoints

### Authentication (`/api/auth/`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/register` | User registration |
| POST | `/api/auth/login` | User login (sets session cookie) |
| POST | `/api/auth/logout` | User logout (clears cookie) |
| GET | `/api/auth/me` | Get current user |

### Resources (`/api/resources/`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/resources` | List resources (filtered by user) |
| GET | `/resources/{uri}` | Get specific resource |
| POST | `/resources` | Create new resource |
| PUT | `/resources/{uri}` | Update resource |
| DELETE | `/resources/{uri}` | Delete resource |
| GET | `/resources/search/{query}` | Search resources |
| GET | `/resources/stats/count` | Count resources |
| GET | `/resources/download/{file_id}` | Download/view original file |
| POST | `/resources/upload` | Upload file |
| POST | `/resources/snippet` | Create text snippet |

### Conversations (`/api/conversations/`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/conversations` | List user's conversations |
| POST | `/conversations` | Create conversation |
| GET | `/conversations/{id}` | Get conversation |
| PUT | `/conversations/{id}` | Update conversation |
| DELETE | `/conversations/{id}` | Delete conversation |
| POST | `/conversations/{id}/messages` | Add message |

### Chat (`/api/chat/`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/chat/conversation` | Chat with conversation context |
| POST | `/chat` | Simple chat (no context) |

### GPU/Model Management (`/api/gpu/`, `/api/models/`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/gpu/health` | GPU and model status |
| GET | `/gpu/metrics` | Real-time GPU metrics |
| GET | `/gpu/recommendations` | Optimization recommendations |
| GET | `/models/switch` | List available models |
| POST | `/models/switch` | Switch active model |

### Search (`/api/search/`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/search` | Compound search (keyword + semantic) |
| GET | `/search/suggestions` | Get search suggestions |

### Tools (`/api/tools/`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/tools/execute` | Execute MCP tool |

---

## Frontend Architecture

### SvelteKit Structure

**Routes** (`ui/src/routes/`):
- `/` - Home page
- `/chat` - ChatGPT-like interface
- `/agents/*` - Individual agent pages
- `/resources` - Resource management
- `/search` - Search interface
- `/gpu` - GPU monitoring
- `/settings` - User settings
- `/login`, `/register` - Authentication

**API Proxies** (`ui/src/routes/api/`):
- Pure HTTP proxies to backend
- Session cookie forwarding
- No business logic

**Components** (`ui/src/lib/components/`):
- `Header.svelte` - Navigation header
- `Sidebar.svelte` - Navigation sidebar
- `ConversationSidebar.svelte` - Chat sidebar
- `GPUStatus.svelte` - GPU monitoring
- `ModelSwitcher.svelte` - Model switching
- `MarkdownRenderer.svelte` - Markdown display

**Stores** (`ui/src/lib/stores/`):
- `conversations.js` - Conversation state (API-backed)
- `auth.js` - Authentication state (legacy, being phased out)

**Services** (`ui/src/lib/services/`):
- `chat-api.js` - Chat API client
- API clients for all backend endpoints

### Server-Side Features

**Hooks** (`ui/src/hooks.server.js`):
- Session validation on every request
- User data in `event.locals.user`
- Server-side auth protection

**Layout Server Load** (`ui/src/routes/+layout.server.js`):
- Returns user data to all pages
- Handles public routes (login/register)
- Server-side redirects for auth

---

## Development Workflow

### Setup

1. **Clone and Install**:
```bash
git clone <repo>
cd ai-mcp-toolkit
./setup.sh  # Auto-detects platform and configures
```

2. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with MongoDB, Redis, Ollama settings
```

3. **Start Services**:
```bash
# Terminal 1: Backend
ai-mcp-toolkit serve

# Terminal 2: Frontend
cd ui && npm run dev
```

### Code Quality

**Python**:
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking
- `pytest` - Testing

**Frontend**:
- TypeScript strict mode
- ESLint
- Prettier (via Tailwind)

### Testing

```bash
# Python tests
pytest tests/

# Frontend tests (planned)
npm test
```

---

## Deployment Configuration

### Production Environment

**Hardware**:
- CPU: Intel i9-11900K (16 cores)
- RAM: 128 GB
- GPU: NVIDIA RTX 3070 Ti (8GB VRAM)
- Storage: 6.5 TB
- OS: Ubuntu 25.04

**Software Stack**:
- MongoDB Atlas (cloud cluster)
- Redis (local or cloud)
- Ollama (local with GPU)
- NGINX (reverse proxy)

### Docker Deployment

```bash
docker-compose up -d
```

**Services**:
- `ai-mcp-toolkit` - Main application
- `ollama` - AI model server

### Environment Variables

**Required**:
- `MONGODB_URL` - MongoDB connection string
- `MONGODB_DATABASE` - Database name
- `OLLAMA_HOST` - Ollama host (default: localhost)
- `OLLAMA_PORT` - Ollama port (default: 11434)

**Optional**:
- `REDIS_URL` - Redis connection (for caching)
- `MCP_HOST` - Backend host (default: localhost)
- `MCP_PORT` - Backend port (default: 8000)
- `LOG_LEVEL` - Logging level (default: INFO)

---

## Current Implementation Status

### ✅ Completed Features

**Phase 1.1: Resource Management** (100%):
- ✅ MongoDB Atlas integration
- ✅ Redis cache setup
- ✅ Resource CRUD operations
- ✅ MCP resource handlers
- ✅ REST API endpoints

**Phase 3.4: Security** (100%):
- ✅ User authentication
- ✅ Session management
- ✅ Password hashing
- ✅ Role-based access control
- ✅ Audit logging

**Phase 3.5: Per-User Storage** (100%):
- ✅ Conversation per-user isolation
- ✅ Resource ownership
- ✅ Frontend auth migration

**Phase 3.6: Server-Side Auth** (100%):
- ✅ SvelteKit hooks for session validation
- ✅ Server-side user data passing
- ✅ Proper cookie handling

**Phase 3.7: Local File Storage** (100%):
- ✅ FileStorageService
- ✅ UUID-based file organization
- ✅ Download/view endpoints

**Phase 0: Compound Search** (80%):
- ✅ Text normalization
- ✅ OCR agent
- ✅ Search service enhancements
- ✅ Dynamic category search
- ⏳ Atlas index deployment
- ⏳ Frontend UI updates

### ⏳ In Progress

**Phase 0.4: Compound Search Endpoint**:
- ⏳ Unified `/search` endpoint
- ⏳ Atlas compound queries
- ⏳ Result explainability

### 🔲 Planned

**Phase 1.2: Prompt Templates**:
- Template storage and management
- MCP prompt handlers
- Template UI

**Phase 1.3: Message Handling**:
- Conversation management
- Message threading
- MCP message handlers

**Phase 2: Agent Cooperation**:
- Agent communication protocols
- Shared context system
- Pipeline processing
- Workflow orchestration

---

## Quick Reference Index

### File Locations

**Configuration**:
- `config.yaml` - Main configuration
- `.env` - Environment variables
- `pyproject.toml` - Python dependencies
- `ui/package.json` - Frontend dependencies

**Documentation**:
- `README.md` - Main documentation
- `PROJECT_RULES_AND_CONTEXT.md` - Project rules
- `TECHNOLOGY_FUNCTIONALITY_MAPPING.md` - Tech mapping
- `ENHANCEMENT_TASKS.md` - Task tracking
- `docs/CONFIGURATION.md` - Configuration guide
- `docs/ARCHITECTURE_RULES.md` - Architecture rules

**Key Source Files**:
- `src/ai_mcp_toolkit/server/mcp_server.py` - MCP server
- `src/ai_mcp_toolkit/server/http_server.py` - FastAPI server
- `src/ai_mcp_toolkit/agents/base_agent.py` - Agent base class
- `src/ai_mcp_toolkit/models/database.py` - Database connection
- `ui/src/hooks.server.js` - Server-side hooks
- `ui/src/routes/+layout.server.js` - Layout server load

### Common Commands

**Development**:
```bash
ai-mcp-toolkit serve          # Start backend
ai-mcp-toolkit ui              # Start frontend
ai-mcp-toolkit status          # Check system status
ai-mcp-toolkit agents          # List agents
```

**Model Management**:
```bash
./switch-model.sh qwen2.5:7b   # Switch model
ollama list                     # List models
ollama ps                       # Running models
```

**Database**:
```bash
# MongoDB shell
mongosh <connection_string>

# Redis CLI
redis-cli
```

### Troubleshooting

**Port Conflicts**:
- Backend: Change `MCP_PORT` in `.env`
- Frontend: Change `UI_PORT` in `.env`

**Database Connection**:
- Check MongoDB is running
- Verify connection string in `.env`
- Check network access (Atlas)

**Ollama Issues**:
- Verify Ollama is running: `ollama ps`
- Check model is downloaded: `ollama list`
- Test connection: `curl http://localhost:11434/api/tags`

---

## Documentation Index

### Setup & Configuration
- `README.md` - Main project documentation
- `QUICKSTART.md` - Quick start guide
- `CROSS_PLATFORM_SETUP.md` - Platform-specific setup
- `docs/CONFIGURATION.md` - Configuration details
- `docs/DATABASE_SETUP.md` - Database setup
- `NETWORK_ACCESS_SETUP.md` - Network deployment

### Architecture & Development
- `PROJECT_RULES_AND_CONTEXT.md` - Project rules and context
- `TECHNOLOGY_FUNCTIONALITY_MAPPING.md` - Tech stack mapping
- `TECHNOLOGY_REQUIREMENTS_REPORT.md` - Tech requirements
- `docs/ARCHITECTURE_RULES.md` - Architecture principles
- `CODEBASE_OVERVIEW.md` - This document

### Feature Documentation
- `GPU_ACCELERATION_SETUP.md` - GPU setup guide
- `LOCAL_FILE_STORAGE.md` - File storage system
- `SEMANTIC_SEARCH_GUIDE.md` - Search documentation
- `CHANGELOG.md` - Version history

### Task Tracking
- `ENHANCEMENT_TASKS.md` - Detailed task list
- Various completion summaries (e.g., `AUTH_COMPLETE_SUMMARY.md`)

---

**Generated**: 2025-01-03  
**Maintainer**: Update this document when architecture changes  
**Format**: Markdown with tables and code blocks for clarity

