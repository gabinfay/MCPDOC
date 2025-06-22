# LLMs.txt Agentic RAG Documentation Agent

A Model Context Protocol (MCP) server that dynamically indexes and queries documentation from any `llms.txt` file. This agent allows you to index multiple documentation sources and ask intelligent questions about them using AI-powered search and retrieval.

## Features

- **Dynamic Documentation Indexing**: Index documentation from any URL containing `llms.txt`
- **Multiple Documentation Sources**: Manage and switch between multiple indexed documentation sources
- **AI-Powered Querying**: Ask natural language questions about the documentation
- **Detailed Indexing**: Automatically generates summaries and topic extractions for each document
- **Persistent State**: Remembers indexed documentation sources across restarts
- **Intelligent Caching**: Efficiently caches downloaded content with hash-based invalidation

## Prerequisites

- Python 3.11+
- OpenAI API Key (for detailed indexing)
- Google/Gemini API Key (for documentation querying)

## Installation

1. Clone the repository:
```bash
git clone git@github.com:gabinfay/MCPDOC.git
cd llms_txt_agent
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Cursor Integration

### MCP Configuration

Add the following configuration to your Cursor MCP settings file (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "doc_agent": {
      "command": "/path/to/your/project/.venv/bin/python",
      "args": [
        "/path/to/your/project/doc_agent_server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "GOOGLE_API_KEY": "your_google_api_key_here"
      }
    }
  }
}
```

**Replace the paths** with your actual project location:
- `/path/to/your/project/.venv/bin/python` → Your virtual environment Python path
- `/path/to/your/project/doc_agent_server.py` → Your script location

### Example Configuration
```json
{
  "mcpServers": {
    "doc_agent": {
      "command": "/Users/username/Documents/llms_txt_agent/.venv/bin/python",
      "args": [
        "/Users/username/Documents/llms_txt_agent/doc_agent_server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "sk-proj-...",
        "GOOGLE_API_KEY": "AIzaSy..."
      }
    }
  }
}
```

## Available MCP Tools

### 1. `index_documentation`
**Purpose**: Index a new documentation source from a URL containing `llms.txt`

**Parameters**:
- `url` (string): URL to the `llms.txt` file

**Example Usage in Cursor**:
```
Index the Stripe documentation from https://docs.stripe.com/llms.txt
```

### 2. `ask_doc_agent`
**Purpose**: Ask questions about the currently active documentation

**Parameters**:
- `query` (string): Your question about the documentation

**Example Usage in Cursor**:
```
What are the main payment methods supported by Stripe?
How do I set up webhooks?
Explain the difference between Payment Intents and Setup Intents
```

### 3. `list_documentation_sources`
**Purpose**: List all indexed documentation sources

**Example Usage in Cursor**:
```
Show me all the documentation sources I have indexed
List available documentation sources
```

### 4. `set_active_documentation`
**Purpose**: Switch to a different indexed documentation source

**Parameters**:
- `url` (string): URL of the documentation source to activate

**Example Usage in Cursor**:
```
Switch to the Stripe documentation
Set the active documentation to https://docs.stripe.com/llms.txt
```

## Example Workflows

### Getting Started
1. **Index your first documentation source**:
   ```
   Index the documentation from https://docs.stripe.com/llms.txt
   ```

2. **Ask questions about it**:
   ```
   What is Stripe and what are its main features?
   ```

3. **Add more documentation sources**:
   ```
   Index the LiveKit documentation from https://docs.livekit.io/llms.txt
   ```

4. **Switch between sources**:
   ```
   List all my documentation sources
   Switch to the LiveKit documentation
   How do I create a video call with LiveKit?
   ```

### Advanced Usage
- **Compare different services**:
  ```
  Index both Stripe and another payment processor's docs, then ask:
  "What are the key differences between Stripe and [other service] for handling subscriptions?"
  ```

- **Deep technical questions**:
  ```
  What are the security best practices for handling webhooks in Stripe?
  Show me examples of error handling in the Stripe API
  ```

## Supported Documentation Sources

Any website that provides an `llms.txt` file can be indexed. Popular examples include:

- **Stripe**: `https://docs.stripe.com/llms.txt`
- **LiveKit**: `https://docs.livekit.io/llms.txt`
- **Mem0**: `https://raw.githubusercontent.com/mem0ai/mem0/main/docs/llms.txt`

## How It Works

1. **Indexing Process**:
   - Downloads the `llms.txt` file from the provided URL
   - Parses markdown file references
   - Downloads all referenced documentation files
   - Generates AI-powered summaries and topic extractions
   - Stores everything locally with intelligent caching

2. **Querying Process**:
   - Uses the detailed index to find relevant documents
   - Reads specific files based on your query
   - Uses Google's Gemini AI to provide intelligent answers
   - Cites sources from the documentation

3. **Caching**:
   - Stores documentation locally in `.doc_agent_cache/`
   - Uses content hashing for efficient updates
   - Preserves state across server restarts

## Troubleshooting

### MCP Server Not Starting
- Check that your API keys are correctly set in the environment
- Verify the Python path in your MCP configuration
- Ensure all dependencies are installed in the virtual environment

### Indexing Failures
- Verify the URL contains a valid `llms.txt` file
- Check your internet connection
- Ensure you have sufficient disk space for caching

### Query Errors
- Make sure you have at least one documentation source indexed
- Verify your Google/Gemini API key is valid and has quota
- Check that the documentation source is properly activated

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section above
- Verify your MCP configuration matches the examples 