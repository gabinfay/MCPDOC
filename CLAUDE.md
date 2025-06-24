# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server that provides an agentic RAG documentation agent. It dynamically indexes and queries documentation from `llms.txt` files or scrapes websites that don't provide llms.txt format. The system allows indexing multiple documentation sources and answering natural language questions about them.

## Development Commands

```bash
# Set up development environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the MCP server directly for testing
python doc_agent_server.py

# Test the server with example client
python simple_official_client.py

# Test documentation parsing utilities
python llms_docs_parser.py
python supabase_docs_parser.py
```

## Architecture

### Core Components

- **`doc_agent_server.py`**: Main MCP server implementing FastMCP with 5 tools:
  - `index_documentation`: Index docs from llms.txt URLs
  - `ask_doc_agent`: Query indexed documentation using Google Gemini
  - `list_documentation_sources`: List all indexed sources
  - `set_active_documentation`: Switch between documentation sources
  - `scrape_and_index_documentation`: Scrape websites without llms.txt

- **Documentation Parsers**: Specialized parsers for different documentation formats:
  - `llms_docs_parser.py`: General-purpose llms.txt parser with section extraction
  - `supabase_docs_parser.py`: Supabase-specific documentation parser

### Key Dependencies

- **MCP Framework**: `mcp` for Model Context Protocol server implementation
- **AI Services**: `google-genai`, `google-adk` for document querying, `openai` for indexing
- **Web Scraping**: `playwright`, `beautifulsoup4`, `markdownify` for sites without llms.txt
- **HTTP**: `httpx`, `requests` for document retrieval

### Data Flow

1. **Indexing**: Downloads llms.txt → parses markdown references → downloads docs → generates AI summaries → caches locally in `.doc_agent_cache/`
2. **Querying**: Uses detailed index → finds relevant docs → reads specific files → uses Gemini AI for answers with citations
3. **State Management**: Persists indexed sources and active documentation across restarts

### Environment Variables

Required for operation:
- `OPENAI_API_KEY`: For detailed document indexing and summarization
- `GOOGLE_API_KEY`: For documentation querying via Gemini

### MCP Integration

Designed to work with Cursor via MCP configuration in `~/.cursor/mcp.json`. The server provides tools for documentation indexing and intelligent querying that can be used directly in Cursor chat.

### Caching Strategy

- Content-based hashing for efficient updates
- Local storage in `.doc_agent_cache/` directory
- State persistence across server restarts
- Intelligent cache invalidation based on content changes