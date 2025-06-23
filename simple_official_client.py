import asyncio
import os
import json
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

# Test URLs for dynamic indexing
TEST_URLS = [
    "https://raw.githubusercontent.com/mem0ai/mem0/main/docs/llms.txt",  # Mem0 docs
    "https://docs.stripe.com/llms.txt",  # Stripe API docs
    "https://docs.livekit.io/llms.txt"  # LiveKit docs
]

# Test URLs for scraping (sites that don't provide llms.txt)
SCRAPING_TEST_URLS = [
    {"url": "https://platform.openai.com/docs", "keep_pattern": "https://platform.openai.com/docs"},  # OpenAI docs
    {"url": "https://docs.anthropic.com/", "keep_pattern": "https://docs.anthropic.com/"},  # Anthropic docs
]

async def test_dynamic_indexing():
    """Test the new dynamic documentation indexing functionality"""
    print("=== Testing Dynamic Documentation Indexing ===")
    
    # Start server without initial URL
    server_env = os.environ.copy()
    # Don't set URL_TO_LLMSTXT to test dynamic indexing
    server_env.pop("URL_TO_LLMSTXT", None)  # Remove if exists
    
    # Ensure API keys are passed
    server_env["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")
    server_env["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
    server_env["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

    server_params = StdioServerParameters(
        command='.venv/bin/python', 
        args=['doc_agent_server.py'],
        env=server_env
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Test 1: List documentation sources (should be empty initially)
            print("\n1. Listing initial documentation sources...")
            result = await session.call_tool('list_documentation_sources', {})
            print("Result:", result)
            
            # Test 2: Index first documentation source
            print(f"\n2. Indexing first documentation source: {TEST_URLS[0]}")
            result = await session.call_tool('index_documentation', {'url': TEST_URLS[0]})
            print("Result:", result)
            
            # Test 3: List documentation sources (should show one now)
            print("\n3. Listing documentation sources after indexing one...")
            result = await session.call_tool('list_documentation_sources', {})
            print("Result:", result)
            
            # Test 4: Ask a question using the indexed documentation
            print("\n4. Asking a question using the indexed documentation...")
            query = "What is mem0 and what are its main capabilities?"
            result = await session.call_tool('ask_doc_agent', {'query': query})
            print("Query:", query)
            print("Answer:", result)
            
            # Test 5: Index a second documentation source (if different URL)
            if len(TEST_URLS) > 1 and TEST_URLS[1] != TEST_URLS[0]:
                print(f"\n5. Indexing second documentation source: {TEST_URLS[1]}")
                result = await session.call_tool('index_documentation', {'url': TEST_URLS[1]})
                print("Result:", result)
                
                # Test 6: List all documentation sources
                print("\n6. Listing all documentation sources...")
                result = await session.call_tool('list_documentation_sources', {})
                print("Result:", result)
                
                # Test 7: Switch to first documentation source
                print(f"\n7. Switching back to first documentation source: {TEST_URLS[0]}")
                result = await session.call_tool('set_active_documentation', {'url': TEST_URLS[0]})
                print("Result:", result)
            else:
                print("\n5-7. Skipping multiple documentation source tests (same URL)")

async def test_existing_cache_detection():
    """Test if the server detects existing cached documentation"""
    print("=== Testing Existing Cache Detection ===")
    
    # Start server without initial URL
    server_env = os.environ.copy()
    # Don't set URL_TO_LLMSTXT to test dynamic indexing
    server_env.pop("URL_TO_LLMSTXT", None)  # Remove if exists
    
    # Ensure API keys are passed
    server_env["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")
    server_env["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
    
    server_params = StdioServerParameters(
        command="python",
        args=["doc_agent_server.py"],
        env=server_env
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print("1. Listing existing documentation sources...")
            result = await session.call_tool('list_documentation_sources', {})
            print(f"   Result: {result}")
            
            if "No documentation sources" not in result:
                print("2. Asking a question to test active documentation...")
                question_result = await session.call_tool('ask_doc_agent', {'query': 'What is this documentation about?'})
                print(f"   Question result: {question_result[:200]}...")
            else:
                print("2. No existing documentation found, indexing Stripe docs...")
                stripe_result = await session.call_tool('index_documentation', {'url': 'https://docs.stripe.com/llms.txt'})
                print(f"   Stripe indexing result: {stripe_result}")

async def test_scraping_functionality():
    """Test the new scraping and indexing functionality"""
    print("=== Testing Scraping and Indexing Functionality ===")
    
    # Start server without initial URL
    server_env = os.environ.copy()
    server_env.pop("URL_TO_LLMSTXT", None)  # Remove if exists
    
    # Ensure API keys are passed
    server_env["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")
    server_env["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
    server_env["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

    server_params = StdioServerParameters(
        command='.venv/bin/python', 
        args=['doc_agent_server.py'],
        env=server_env
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Test 1: List initial documentation sources
            print("\n1. Listing initial documentation sources...")
            result = await session.call_tool('list_documentation_sources', {})
            print("Result:", result)
            
            # Test 2: Try scraping a documentation site
            # Let's start with a simple one - we'll use a basic docs site
            test_url = "https://platform.openai.com/docs"  # OpenAI has good docs structure
            keep_pattern = "https://platform.openai.com/docs"
            max_pages = 5  # Keep it small for testing
            
            print(f"\n2. Scraping documentation from: {test_url}")
            print(f"   Keep pattern: {keep_pattern}")
            print(f"   Max pages: {max_pages}")
            result = await session.call_tool('scrape_and_index_documentation', {
                'start_url': test_url,
                'keep_url_pattern': keep_pattern,
                'max_pages': max_pages
            })
            print("Scraping result:", result)
            
            # Test 3: List documentation sources after scraping
            print("\n3. Listing documentation sources after scraping...")
            result = await session.call_tool('list_documentation_sources', {})
            print("Result:", result)
            
            # Test 4: Ask a question using the scraped documentation
            if "Successfully scraped and indexed" in str(result):
                print("\n4. Asking a question using the scraped documentation...")
                query = "What is the OpenAI API and how do I get started?"
                result = await session.call_tool('ask_doc_agent', {'query': query})
                print("Query:", query)
                print("Answer:", result[:500] + "..." if len(result) > 500 else result)
            else:
                print("\n4. Skipping question test - scraping may have failed")
            
            # Test 5: Test basic functionality (fallback)
            print("\n5. Testing basic functionality...")
            result = await session.call_tool('test_basic_functionality', {})
            print("Basic functionality test:", result)

async def client():
    """Original client functionality for backward compatibility"""
    url_to_use = os.getenv("TEST_URL_TO_LLMSTXT", "https://raw.githubusercontent.com/mem0ai/mem0/main/docs/llms.txt")
    print(f"Client: Configuring server to use URL_TO_LLMSTXT: {url_to_use}")

    server_env = os.environ.copy()
    server_env["URL_TO_LLMSTXT"] = url_to_use
    server_env["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")
    server_env["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
    server_env["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

    server_params = StdioServerParameters(
        command='.venv/bin/python', 
        args=['doc_agent_server.py'],
        env=server_env
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            query = "What is graph memory in mem0 and how does it enhance the memory retrieval process? Please provide examples and cite your sources."
            print(f"Client: Sending query: {query}")
            result_from_tool = await session.call_tool('ask_doc_agent', {'query': query})
            print("Client: Received result:")
            
            response_content = result_from_tool 
            try:
                if isinstance(response_content, str):
                    if response_content.strip().startswith("{") or response_content.strip().startswith("["):
                        try:
                            parsed_result = json.loads(response_content)
                            print(json.dumps(parsed_result, indent=2))
                        except json.JSONDecodeError:
                            print(response_content)
                    else:
                        print(response_content)
                else:
                    print(repr(response_content)) 
            except Exception as e:
                print(f"Error during result processing: {e!r}")
                print("Raw result from tool:", repr(result_from_tool))

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    # Choose which test to run
    test_mode = os.getenv("TEST_MODE", "dynamic")  # "dynamic", "existing_cache", "scraping", or "legacy"
    
    if test_mode == "dynamic":
        asyncio.run(test_dynamic_indexing())
    elif test_mode == "existing_cache":
        asyncio.run(test_existing_cache_detection())
    elif test_mode == "scraping":
        asyncio.run(test_scraping_functionality())
    else:
        asyncio.run(client())