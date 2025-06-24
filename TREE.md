# Project Structure

*   `MCPDOC-clean/` - Root directory for the Agentic RAG Documentation Agent.
    *   `references/` - Contains reference materials, examples, and standalone scripts.
        *   `complete_docs_scraper.py` - A standalone, advanced Python script for scraping documentation websites. It can create local copies, `llms.txt`, and `llms-full.txt`.
        *   `layerzero_llms.txt` - An example `llms.txt` file for LayerZero V2 documentation, used as input for the indexing tool.
        *   `supabase.txt` - A large, pre-formatted text file containing the Supabase Python reference documentation, likely used as input for a specialized parser.
    *   `CLAUDE.md` - A markdown file providing guidance to an AI assistant (Claude) for working with this repository, containing project overview, commands, and architecture.
    *   `doc_agent_server.py` - The core of the project. It's an MCP server that indexes documentation (from `llms.txt` or scraping) and answers questions about it using AI.
        *   **Main Features**:
            *   Dynamic documentation indexing from URLs or scraping.
            *   Manages multiple documentation sources.
            *   Provides AI-powered querying via Google Gemini.
            *   Includes tools: `index_documentation`, `ask_doc_agent`, `list_documentation_sources`, `set_active_documentation`, `scrape_and_index_documentation`.
            *   Persistent state and caching.
    *   `future_version_mcpdoc.png` - An image file, likely a mockup or diagram for a future version of the project.
    *   `mcpdoc.png` - The project's logo image.
    *   `README.md` - The main documentation for the project, explaining features, setup, usage, and available tools.
    *   `requirements.txt` - A text file listing the Python dependencies required for the project.
    *   `simple_official_client.py` - A Python script for testing the `doc_agent_server.py`.
        *   **Main Features**:
            *   Provides test suites for dynamic indexing, cache detection, and scraping.
            *   Demonstrates programmatic interaction with the MCP server.
            *   Not intended for end-users.
