<h1 align="center"><img src="https://user-images.githubusercontent.com/26521948/72658109-63a1d400-39e7-11ea-9667-c652586b4508.png" alt="Apache JMeter logo" /></h1>
<h4 align="center">SOFTWARE TESTING ENTHUSIAST</h4>
<br>

# 🚀 Mini RAG - Your Personal AI Document Assistant

A powerful, production-ready RAG (Retrieval-Augmented Generation) system that runs entirely on your local machine using Ollama for AI models and Qdrant for vector storage.

## ✨ Features

- **🤖 Local AI Models**: Uses Ollama with llama3.1:8b and nomic-embed-text
- **🗄️ Persistent Storage**: Qdrant vector database for document embeddings
- **🔐 Secure Authentication**: JWT-based login system with role-based access
- **🌐 Beautiful Web UI**: Modern, responsive interface for document management
- **📁 Multi-Format Support**: PDF, Markdown, and text files
- **💬 Interactive Chat**: Ask questions with normal or streaming responses
- **📊 Source Citations**: Get answers with document references
- **🐳 Docker Ready**: Complete containerized setup for easy deployment
- **📱 Responsive Design**: Works on desktop and mobile devices
- **👥 User Management**: Admin and user roles with different permissions

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser  │    │   RAG API      │    │  Qdrant Vector │
│                 │◄──►│   (FastAPI)    │◄──►│   Database     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Ollama API    │
                       │  (AI Models)    │
                       └─────────────────┘
```

## ⚡️ Quick Start

Prerequisites:
- Docker Desktop — `https://www.docker.com/products/docker-desktop/`
- Ollama — `https://ollama.com`

Setup:
```bash
# 1) Download AI models (one-time)
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# 2) Start services
make start-app

# 3) Open the app
# Web UI:  http://localhost:8000
# API Docs: http://localhost:8000/docs (access it from Web UI)

# 4) Stop / Restart
make stop-app
make restart-app
```

## 🧱 Tech Stack
- Python (FastAPI, Pydantic v2)
- Qdrant (vector DB)
- Ollama (local models)
- Playwright (E2E), Pytest (unit), Newman (API)
- Docker + Makefile workflow

## 📦 Project Layout
- `src/` — FastAPI app and services
- `templates/` — server-rendered HTML
- `tests/` — unit/integration tests
- `e2e-tests/` — Playwright tests
- `scripts/` — helper scripts (tests, typecheck)

## 🧪 Testing

### Makefile Commands
```bash
make test                 # unit tests
make test-api             # Postman/Newman API tests
make test-e2e-chromium    # E2E (Chromium only)
make test-typecheck       # mypy (strict)
make test-mutation        # full mutation run (slower)
```

### Advanced Unit Test Script (`./scripts/test-unit`)
The unit test script provides comprehensive testing options with detailed reporting:

#### Basic Usage
```bash
./scripts/test-unit                    # Run all unit tests
./scripts/test-unit --fast             # Quick run (quiet, no coverage)
./scripts/test-unit --coverage         # With coverage summary
./scripts/test-unit --stop-on-fail     # Stop on first failure
./scripts/test-unit --parallel         # Run tests in parallel
```

#### Filtering & Targeting
```bash
./scripts/test-unit -k auth            # Filter by keyword (auth tests)
./scripts/test-unit --streaming        # Run only streaming tests
./scripts/test-unit --regression       # Run regression test subset
```

#### Reports & Coverage
```bash
./scripts/test-unit --coverage --html --open-reports    # Coverage + HTML report
./scripts/test-unit --coverage --html --parallel -k auth # Combined options
```

#### Maintenance
```bash
./scripts/test-unit --skip-deps        # Skip dependency checks
./scripts/test-unit --clean            # Clean test artifacts
./scripts/test-unit --install-deps     # Install/update dependencies
```

## 🌐 Web Interface
| Service | URL |
|--------|-----|
| 🌐 Web UI | http://localhost:8000 |
| 🗄️ Qdrant | http://localhost:6333/dashboard |

## 🛠 Usage Examples
```bash
# Health (no auth)
curl http://localhost:8000/health

# Login → token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | jq -r .access_token)

# Ask a question (auth)
curl -s -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"What is this document about?"}' | jq
```

## 🆘 Troubleshooting (quick)
- App not ready? `make restart-app` and open /health
- Missing models? `ollama pull llama3.1:8b` and `ollama pull nomic-embed-text`

## Demo in Youtube - Windows
   <a href="https://youtu.be/iPN_4nwQOOA" target="_blank"><img src="https://user-images.githubusercontent.com/26521948/72658109-63a1d400-39e7-11ea-9667-c652586b4508.png" 
   alt="CLICK HERE" width="140" height="80" border="10" /></a>

## 📜 License
Open source by Okta Liem. Use and modify as needed.
