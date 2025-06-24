import asyncio
import os
from doc_agent_server import (
    index_preformatted_markdown,
    ask_doc_agent,
    set_active_documentation,
    main_async
)

async def run_full_test():
    """
    Runs a full end-to-end test:
    1. Initializes the doc agent server environment.
    2. Indexes documentation from a URL using `index_preformatted_markdown`.
    3. Sets the newly indexed doc as active.
    4. Asks a question to the agent to test retrieval.
    """
    # --- Phase 1: Environment Setup ---
    print("▶️ Initializing server environment...")
    # This ensures cache directories exist and state is loaded.
    await main_async()
    print("✅ Environment initialized.")

    # --- Phase 2: Indexing ---
    test_url = "https://supabase.com/llms/python.txt"
    test_project_name = 'supabase_from_url'

    print(f"\n▶️ Running test for `index_preformatted_markdown` with URL...")
    print(f"  URL: '{test_url}'")
    print(f"  Project: '{test_project_name}'")

    indexing_result = await index_preformatted_markdown(
        url=test_url,
        project_name=test_project_name
    )
    print("\n--- Indexing Result ---")
    print(indexing_result)
    print("-----------------------\n")

    if "ERROR" in indexing_result:
        print("❌ Test failed during indexing phase.")
        return

    # --- Phase 3: Set Active and Test Retrieval ---
    print(f"▶️ Setting active documentation to '{test_url}'...")
    active_result = await set_active_documentation(url=test_url)
    print(f"  Result: {active_result}\n")

    retrieval_query = "How do I create a bucket in storage?"
    print(f"▶️ Testing retrieval with query: '{retrieval_query}'")

    retrieval_result = await ask_doc_agent(query=retrieval_query)
    
    print("\n--- Retrieval Result ---")
    print(retrieval_result)
    print("------------------------\n")
    
    if "ERROR" in retrieval_result or "could not find" in retrieval_result.lower():
         print("❌ Test failed during retrieval phase.")
    else:
        print("✅ Retrieval test appears successful.")

    print("\n⏹️ Full test complete.")


if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(run_full_test()) 