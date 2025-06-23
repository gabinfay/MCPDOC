import sys
import logging
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import asyncio
import os
import hashlib # For generating unique cache directory names
import httpx # For asynchronous HTTP requests
from urllib.parse import urlparse, urljoin, unquote # For URL manipulation
import re # For regular expressions
import openai # Added for V3
import json # For state persistence
import time # For scraping delays
from bs4 import BeautifulSoup # For HTML parsing in scraping
from markdownify import markdownify as md # For converting HTML to markdown
from playwright.async_api import async_playwright # For JavaScript-heavy pages
from concurrent.futures import ThreadPoolExecutor # For parallel processing

from google.genai import types
import google.adk # For version and path checking
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.function_tool import FunctionTool

load_dotenv()

print(f"DEBUG: google.adk version: {getattr(google.adk, '__version__', 'N/A')}", file=sys.stderr)
print(f"DEBUG: google.adk path: {getattr(google.adk, '__path__', 'N/A')}", file=sys.stderr)

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

mcp_server = FastMCP("DocumentationAgentMCPV3") # Updated name for V3

# --- Global variables for paths and master index content ---
DOCS_ROOT_PATH_ABS = None # Will be set dynamically
MASTER_INDEX_CONTENT = None # Simple index
DETAILED_INDEX_CONTENT = None # For V3: LLM-generated detailed index
BASE_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".doc_agent_cache")

# NEW: Support for multiple documentation sources
INDEXED_DOCS = {} # {url: {'cache_dir': str, 'project_name': str, 'detailed_index_content': str, 'master_index_content': str}}
CURRENT_ACTIVE_DOC = None # Currently active documentation source URL
INDEXED_DOCS_STATE_FILE = os.path.join(BASE_CACHE_DIR, ".indexed_docs_state.json")

# --- End of global variables ---

def extract_project_name_from_llmstxt(llmstxt_content: str) -> str:
    """
    Extracts the project name from llms.txt content.
    Looks for the first H1 header (# Project Name) and returns a filesystem-safe version.
    Falls back to 'unknown_project' if no valid title is found.
    """
    try:
        lines = llmstxt_content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# ') and len(line) > 2:
                # Extract the project name from the H1 header
                project_name = line[2:].strip()
                if project_name:
                    # Make it filesystem-safe by removing/replacing invalid characters
                    # Keep alphanumeric, hyphens, underscores, and spaces (convert spaces to underscores)
                    safe_name = re.sub(r'[^\w\s-]', '', project_name)
                    safe_name = re.sub(r'\s+', '_', safe_name)
                    safe_name = safe_name.strip('_-')
                    if safe_name:
                        logger.info(f"Extracted project name: '{project_name}' -> filesystem-safe: '{safe_name}'")
                        return safe_name
        
        # If no H1 header found, fallback to 'unknown_project'
        logger.warning("No H1 header found in llms.txt content. Using fallback name.")
        return "unknown_project"
    except Exception as e:
        logger.error(f"Error extracting project name from llms.txt: {e}")
        return "unknown_project"


def get_unique_cache_dir_name(project_name: str, url_to_llmstxt: str) -> str:
    """
    Creates a unique cache directory name based on project name.
    If the project_name directory already exists, adds a suffix based on URL hash.
    """
    base_name = project_name
    full_path = os.path.join(BASE_CACHE_DIR, base_name)
    
    # If directory doesn't exist, we can use the project name as-is
    if not os.path.exists(full_path):
        return base_name
    
    # If it exists, check if it's for the same URL by checking a URL marker file
    url_marker_file = os.path.join(full_path, ".source_url")
    if os.path.exists(url_marker_file):
        try:
            with open(url_marker_file, 'r', encoding='utf-8') as f:
                stored_url = f.read().strip()
            if stored_url == url_to_llmstxt:
                # Same URL, we can reuse this directory
                logger.info(f"Reusing existing cache directory for same URL: {full_path}")
                return base_name
        except Exception as e:
            logger.warning(f"Could not read URL marker file {url_marker_file}: {e}")
    
    # Different URL or can't determine, create a unique suffix
    url_hash = hashlib.md5(url_to_llmstxt.encode('utf-8')).hexdigest()[:8]
    unique_name = f"{base_name}_{url_hash}"
    logger.info(f"Cache directory exists for different source. Using unique name: {unique_name}")
    return unique_name


def create_url_marker_file(cache_dir: str, url_to_llmstxt: str):
    """Creates a marker file to track which URL this cache directory is for."""
    try:
        url_marker_file = os.path.join(cache_dir, ".source_url")
        with open(url_marker_file, 'w', encoding='utf-8') as f:
            f.write(url_to_llmstxt)
        logger.info(f"Created URL marker file: {url_marker_file}")
    except Exception as e:
        logger.warning(f"Failed to create URL marker file: {e}")


def get_llms_full_url(llms_txt_url: str) -> str:
    """Convert llms.txt URL to llms-full.txt URL."""
    if llms_txt_url.endswith('/llms.txt'):
        return llms_txt_url[:-9] + '/llms-full.txt'  # Replace 'llms.txt' with 'llms-full.txt'
    elif llms_txt_url.endswith('llms.txt'):
        return llms_txt_url[:-8] + 'llms-full.txt'  # Replace 'llms.txt' with 'llms-full.txt'
    else:
        # Fallback: append llms-full.txt to the base URL
        base_url = llms_txt_url.rsplit('/', 1)[0] if '/' in llms_txt_url else llms_txt_url
        return f"{base_url}/llms-full.txt"


def compute_content_hash(content: str) -> str:
    """Compute SHA256 hash of content for cache invalidation."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def save_llms_full_hash(cache_dir: str, content_hash: str):
    """Save the hash of llms-full.txt content for cache validation."""
    try:
        hash_file = os.path.join(cache_dir, ".llms_full_hash")
        with open(hash_file, 'w', encoding='utf-8') as f:
            f.write(content_hash)
        logger.info(f"Saved llms-full.txt hash: {content_hash}")
    except Exception as e:
        logger.warning(f"Failed to save llms-full.txt hash: {e}")


def get_saved_llms_full_hash(cache_dir: str) -> str | None:
    """Get the previously saved hash of llms-full.txt content."""
    try:
        hash_file = os.path.join(cache_dir, ".llms_full_hash")
        if os.path.exists(hash_file):
            with open(hash_file, 'r', encoding='utf-8') as f:
                saved_hash = f.read().strip()
                logger.info(f"Retrieved saved llms-full.txt hash: {saved_hash}")
                return saved_hash
    except Exception as e:
        logger.warning(f"Failed to read saved llms-full.txt hash: {e}")
    return None


def get_local_path_from_url(main_index_url_str: str, file_url_str: str, unique_cache_root_abs: str) -> str | None:
    """
    Derives a local file path within the unique_cache_root_abs based on the file's URL
    relative to the main_index_url_str's domain and path.
    """
    try:
        main_index_parsed = urlparse(main_index_url_str)
        file_parsed = urlparse(file_url_str)

        if not file_parsed.scheme or not file_parsed.netloc:
            # Handle relative URLs within the llms.txt if any (resolve against main_index_url_str)
            absolute_file_url = urljoin(main_index_url_str, file_url_str)
            file_parsed = urlparse(absolute_file_url)
        
        if main_index_parsed.netloc != file_parsed.netloc:
            logger.warning(f"File URL {file_url_str} is on a different domain than main index {main_index_url_str}. Using full path from file URL for local structure.")
            relative_path = file_parsed.path.lstrip('/')
        else:
            main_index_dir_path = os.path.dirname(main_index_parsed.path) 
            if file_parsed.path.startswith(main_index_dir_path) and main_index_dir_path != '/':
                relative_path = file_parsed.path[len(main_index_dir_path):].lstrip('/')
            else: 
                relative_path = file_parsed.path.lstrip('/')
        
        if not relative_path: 
            relative_path = "_root_index.md" 
            logger.warning(f"File URL {file_url_str} seems to be a domain root. Saving as {relative_path}")

        if ".." in relative_path.split(os.sep) or os.path.isabs(relative_path):
            logger.error(f"Invalid relative path derived: {relative_path} from {file_url_str}. Skipping.")
            return None

        local_file_path = os.path.join(unique_cache_root_abs, relative_path)
        return os.path.normpath(local_file_path)
        
    except Exception as e:
        logger.error(f"Error in get_local_path_from_url for main='{main_index_url_str}', file='{file_url_str}': {e}", exc_info=True)
        return None


async def download_file(url: str, session: httpx.AsyncClient, timeout_seconds: int = 30) -> str | None:
    """Downloads content of a given URL."""
    try:
        logger.info(f"Attempting to download: {url}")
        response = await session.get(url, follow_redirects=True, timeout=timeout_seconds)
        response.raise_for_status() 
        logger.info(f"Successfully downloaded: {url} (status: {response.status_code})")
        return response.text
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code} while downloading {url}: {e.response.text[:200]}...")
    except httpx.RequestError as e:
        logger.error(f"Request error while downloading {url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}", exc_info=True)
    return None

async def get_summary_for_file_content_async(file_content: str, file_path_for_context: str, model_name: str = "gpt-4o-mini") -> str:
    """Uses OpenAI to generate a summary, extract topics, and list sections for a file's content."""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error(f"OPENAI_API_KEY not found. Cannot generate summary for {file_path_for_context}.")
        return "Error: OPENAI_API_KEY not configured. Summary generation skipped."

    client = openai.AsyncOpenAI(api_key=openai_api_key)
    system_prompt = "You are an expert technical writer. Your task is to analyze the following markdown document content and provide a structured summary."
    user_prompt = f"""Please analyze the content of the document located at '{file_path_for_context}'.
Provide the following in markdown format:
1.  **Overall Summary:** A concise (2-3 sentences) overview of the document's main purpose and key information.
2.  **Main Topics:** A bulleted list of the primary topics or concepts discussed.
3.  **Major Sections:** A bulleted list of the most important H1, H2, or H3 level section headings found in the document. If no clear headings, state so.

Content to analyze:
---
{file_content[:15000]} 
---
""" # Limiting content to avoid excessive token usage for summarization

    try:
        logger.info(f"Requesting summary from OpenAI for: {file_path_for_context} using model {model_name}")
        completion = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2, # Lower temperature for more factual summaries
        )
        summary = completion.choices[0].message.content
        logger.info(f"Successfully generated summary for: {file_path_for_context}")
        return summary.strip() if summary else "No summary could be generated."
    except Exception as e:
        logger.error(f"Error calling OpenAI for summary of {file_path_for_context}: {e}", exc_info=True)
        return f"Error during summary generation for {file_path_for_context}: {str(e)}"


async def generate_detailed_index_async(cache_dir_path: str, downloaded_files_map: dict[str, str]) -> str | None:
    """
    Generates a detailed_index.md file by summarizing each downloaded markdown file in parallel.
    downloaded_files_map: {local_abs_path: original_url}
    Returns the absolute path to the generated detailed_index.md or None on failure.
    """
    logger.info(f"Starting parallel detailed index generation for cache directory: {cache_dir_path}")
    detailed_index_file_path = os.path.join(cache_dir_path, "detailed_index.md")

    sorted_local_paths = sorted(downloaded_files_map.keys()) # Process in a consistent order

    # Prepare data for parallel processing
    file_data = []
    for local_abs_path in sorted_local_paths:
        original_url = downloaded_files_map[local_abs_path]
        relative_path_to_cache_root = os.path.relpath(local_abs_path, cache_dir_path)
        
        try:
            with open(local_abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            file_data.append((local_abs_path, original_url, relative_path_to_cache_root, content))
        except Exception as e:
            logger.error(f"Failed to read file {local_abs_path} for detailed index: {e}", exc_info=True)
            file_data.append((local_abs_path, original_url, relative_path_to_cache_root, None))

    # Create summarization tasks with rate limiting to avoid overwhelming OpenAI API
    summarization_tasks = []
    file_metadata = []  # Store metadata for each file
    
    for local_abs_path, original_url, relative_path, content in file_data:
        file_metadata.append((local_abs_path, original_url, relative_path, content))
        
        if content and content.strip():
            # Create actual async task for summarization
            task = get_summary_for_file_content_async(content, relative_path)
            summarization_tasks.append(task)
        else:
            # Create a simple async function for empty files
            async def create_empty_summary():
                return "File is empty or contains only whitespace."
            summarization_tasks.append(create_empty_summary())

    logger.info(f"Starting {len(summarization_tasks)} parallel summarization tasks with rate limiting...")
    
    # Process in batches to avoid overwhelming the API
    batch_size = 10  # Process 10 files at a time
    summary_results = []
    
    for i in range(0, len(summarization_tasks), batch_size):
        batch = summarization_tasks[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(summarization_tasks) + batch_size - 1) // batch_size
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} files)...")
        
        try:
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            summary_results.extend(batch_results)
            logger.info(f"Completed batch {batch_num}/{total_batches}")
            
            # Add a small delay between batches to be respectful to the API
            if i + batch_size < len(summarization_tasks):
                await asyncio.sleep(2)  # 2 second delay between batches
                
        except Exception as e:
            logger.error(f"Error during batch {batch_num} summarization: {e}", exc_info=True)
            # Fallback to individual processing for this batch
            for task in batch:
                try:
                    result = await task
                    summary_results.append(result)
                except Exception as task_error:
                    summary_results.append(f"Error: {str(task_error)}")
    
    logger.info(f"Completed all {len(summary_results)} summarization tasks")
    
    # Build the detailed index with the parallel results
    detailed_index_entries = ["# Detailed Documentation Index\n\n"]
    
    for i, (local_abs_path, original_url, relative_path, content) in enumerate(file_metadata):
        entry_header = f"## File: `{relative_path}`\n"
        entry_header += f"- Original URL: <{original_url}>\n\n"
        detailed_index_entries.append(entry_header)
        
        # Get the corresponding summary result
        if i < len(summary_results):
            summary_result = summary_results[i]
            if isinstance(summary_result, Exception):
                logger.error(f"Summarization failed for {relative_path}: {summary_result}")
                summary_text = f"Error generating summary for {relative_path}: {str(summary_result)}"
            else:
                summary_text = summary_result
                if not content or not content.strip():
                    logger.info(f"Used cached empty summary for: {local_abs_path}")
        else:
            logger.warning(f"No summary result found for {relative_path}")
            summary_text = f"Error: No summary result available for {relative_path}"
        
        detailed_index_entries.append(summary_text + "\n\n---\n\n")

    try:
        with open(detailed_index_file_path, 'w', encoding='utf-8') as f_idx:
            f_idx.write("".join(detailed_index_entries))
        logger.info(f"Successfully generated and saved detailed index to: {detailed_index_file_path}")
        return detailed_index_file_path
    except Exception as e:
        logger.error(f"Failed to save detailed_index.md to {detailed_index_file_path}: {e}", exc_info=True)
        return None


async def setup_documentation_source(url_to_llmstxt: str) -> tuple[str | None, str | None, str | None]:
    """
    Sets up the documentation source:
    - Creates a unique local cache directory for the url_to_llmstxt.
    - Downloads llms.txt and all referenced markdown files if not already cached.
    - Generates a detailed_index.md for the cached files.
    - Returns (path_to_local_cache_root, llms_txt_content_str, path_to_detailed_index_file).
    """
    try:
        global DOCS_ROOT_PATH_ABS 
        
        logger.info(f"setup_documentation_source called with URL: {url_to_llmstxt}")
        
        if not url_to_llmstxt:
            logger.error("URL_TO_LLMSTXT environment variable is not set. Server cannot start.")
            return None, None, None

        # Test httpx import
        try:
            import httpx
            logger.info("httpx import successful")
        except ImportError as e:
            logger.error(f"httpx import failed: {e}")
            return None, None, None
        
        # Test if we can create httpx client
        try:
            test_client = httpx.AsyncClient()
            await test_client.aclose()
            logger.info("httpx AsyncClient creation test successful")
        except Exception as e:
            logger.error(f"httpx AsyncClient creation failed: {e}")
            return None, None, None
    except Exception as e:
        logger.error(f"Exception in setup_documentation_source early phase: {e}", exc_info=True)
        return None, None, None

    logger.info(f"BASE_CACHE_DIR is: {BASE_CACHE_DIR}")
    if not os.path.exists(BASE_CACHE_DIR):
        try:
            logger.info(f"Creating base cache directory: {BASE_CACHE_DIR}")
            os.makedirs(BASE_CACHE_DIR)
            logger.info(f"Created base cache directory: {BASE_CACHE_DIR}")
        except Exception as e:
            logger.error(f"Failed to create base cache directory {BASE_CACHE_DIR}: {e}", exc_info=True)
            return None, None, None
    else:
        logger.info(f"Base cache directory already exists: {BASE_CACHE_DIR}")

    # First, we need to download both llms.txt and llms-full.txt to extract the project name
    # and determine if we need to recompute summaries based on llms-full.txt hash
    
    try:
        logger.info(f"Creating httpx.AsyncClient for downloading from {url_to_llmstxt}")
        async with httpx.AsyncClient() as temp_client:
            logger.info(f"Starting download of main index file: {url_to_llmstxt}")
            # Download llms.txt for project name and file list
            main_index_content_str = await download_file(url_to_llmstxt, temp_client)
            if not main_index_content_str:
                logger.error(f"Failed to download the main index file from {url_to_llmstxt}.")
                return None, None, None
            
            logger.info(f"Successfully downloaded main index file. Content length: {len(main_index_content_str)}")
            
            # Download llms-full.txt for hash-based cache invalidation
            llms_full_url = get_llms_full_url(url_to_llmstxt)
            logger.info(f"Starting download of llms-full.txt: {llms_full_url}")
            llms_full_content = await download_file(llms_full_url, temp_client)
            if not llms_full_content:
                logger.warning(f"Failed to download llms-full.txt from {llms_full_url}. Using llms.txt hash as fallback.")
                llms_full_content = main_index_content_str  # Fallback to llms.txt content
            else:
                logger.info(f"Successfully downloaded llms-full.txt. Content length: {len(llms_full_content)}")
            
            # Compute hash of llms-full.txt for cache validation
            current_llms_full_hash = compute_content_hash(llms_full_content)
            logger.info(f"Computed content hash: {current_llms_full_hash}")
    except Exception as e:
        logger.error(f"Exception during initial download phase: {e}", exc_info=True)
        return None, None, None
    
    # Extract project name from the downloaded content
    project_name = extract_project_name_from_llmstxt(main_index_content_str)
    unique_cache_dir_name = get_unique_cache_dir_name(project_name, url_to_llmstxt)
    unique_cache_subdir_abs = os.path.join(BASE_CACHE_DIR, unique_cache_dir_name)
    completion_marker_file = os.path.join(unique_cache_subdir_abs, ".download_complete")
    cached_index_file_path = os.path.join(unique_cache_subdir_abs, "_index.txt") # llms.txt content
    detailed_index_md_path = os.path.join(unique_cache_subdir_abs, "detailed_index.md") # V3

    downloaded_files_path_url_map_for_indexing: dict[str, str] = {} # {local_abs_path: original_url}


    if os.path.exists(unique_cache_subdir_abs) and os.path.exists(completion_marker_file):
        # Check if the llms-full.txt hash matches to determine if we need to regenerate summaries
        saved_hash = get_saved_llms_full_hash(unique_cache_subdir_abs)
        hash_matches = saved_hash == current_llms_full_hash
        
        if hash_matches:
            logger.info(f"Hash matches! Using cached documentation for {url_to_llmstxt} from {unique_cache_subdir_abs}")
        else:
            logger.info(f"Hash changed ({saved_hash} != {current_llms_full_hash}). Will regenerate detailed index.")
        
        try:
            with open(cached_index_file_path, 'r', encoding='utf-8') as f:
                index_content_str = f.read()
            
            # Check if detailed_index.md exists and hash matches, if not, regenerate it
            if not os.path.exists(detailed_index_md_path) or not hash_matches:
                if not hash_matches:
                    logger.info(f"Regenerating detailed index due to hash mismatch for {unique_cache_subdir_abs}")
                else:
                    logger.info(f"Detailed index {detailed_index_md_path} not found for cached source. Generating now...")
                
                # Need to reconstruct downloaded_files_path_url_map for indexing
                temp_downloaded_map = {}
                if index_content_str:
                    markdown_links_from_cache = re.findall(r'\[[^\]]*?\]\(([^)]+?)\)', index_content_str)
                    cached_md_urls = []
                    for link_target in markdown_links_from_cache:
                        if link_target.startswith("http://") or link_target.startswith("https://"):
                            cached_md_urls.append(link_target)
                        elif not link_target.startswith("#") and ".md" in link_target:
                            cached_md_urls.append(urljoin(url_to_llmstxt, link_target))
                    
                    for md_url_original in cached_md_urls:
                        local_path_reconstructed = get_local_path_from_url(url_to_llmstxt, md_url_original, unique_cache_subdir_abs)
                        if local_path_reconstructed and os.path.exists(local_path_reconstructed):
                           temp_downloaded_map[local_path_reconstructed] = md_url_original
                
                if not temp_downloaded_map: # Fallback: Walk the directory if llms.txt parsing fails or it's empty
                    logger.warning("Could not reconstruct file map from cached llms.txt for detailed index. Walking directory.")
                    for root, _, files in os.walk(unique_cache_subdir_abs):
                        for fname in files:
                            if fname.endswith(".md") and fname not in ["detailed_index.md", "_index.txt"]: # Avoid indexing the index itself
                                f_abs_path = os.path.join(root, fname)
                                # We don't have the original URL here, so use a placeholder
                                temp_downloaded_map[f_abs_path] = f"local_cached_file://{os.path.relpath(f_abs_path, unique_cache_subdir_abs)}"
                
                generated_detailed_index_path = await generate_detailed_index_async(unique_cache_subdir_abs, temp_downloaded_map)
                if generated_detailed_index_path:
                    # Save the new hash since we regenerated the detailed index
                    save_llms_full_hash(unique_cache_subdir_abs, current_llms_full_hash)
                else:
                    logger.error("Failed to generate detailed index for an existing cache. Proceeding without it for this run.")
            
            DOCS_ROOT_PATH_ABS = unique_cache_subdir_abs
            return unique_cache_subdir_abs, index_content_str, detailed_index_md_path # Return path, content loaded later
        except Exception as e:
            logger.error(f"Failed to read cached index file {cached_index_file_path} or handle detailed index: {e}. Re-downloading.", exc_info=True)
            try: os.remove(completion_marker_file) 
            except: pass
            if os.path.exists(detailed_index_md_path): # Clean up potentially stale detailed index
                try: os.remove(detailed_index_md_path)
                except: pass
    
    logger.info(f"Cache not found or incomplete for {url_to_llmstxt}. Downloading to {unique_cache_subdir_abs}...")
    if not os.path.exists(unique_cache_subdir_abs):
        try:
            os.makedirs(unique_cache_subdir_abs)
        except Exception as e:
            logger.error(f"Failed to create unique cache directory {unique_cache_subdir_abs}: {e}", exc_info=True)
            return None, None, None

    # Create URL marker file to track which URL this cache is for
    create_url_marker_file(unique_cache_subdir_abs, url_to_llmstxt)

    # We already have the main_index_content_str from the earlier download
    # Save it to the cache
    try:
        with open(cached_index_file_path, 'w', encoding='utf-8') as f:
            f.write(main_index_content_str)
        logger.info(f"Saved main index content to {cached_index_file_path}")
    except Exception as e:
        logger.error(f"Failed to save main index content to {cached_index_file_path}: {e}", exc_info=True)
        return None, None, None

    async with httpx.AsyncClient() as client:
        markdown_links = re.findall(r'\[[^\]]*?\]\(([^)]+?)\)', main_index_content_str)
        processed_markdown_urls = []
        for link_target in markdown_links:
            if link_target.startswith("http://") or link_target.startswith("https://"):
                processed_markdown_urls.append(link_target)
            elif not link_target.startswith("#") and ".md" in link_target: 
                absolute_md_url = urljoin(url_to_llmstxt, link_target)
                processed_markdown_urls.append(absolute_md_url)
                logger.info(f"Resolved relative link '{link_target}' to '{absolute_md_url}'")
            else:
                logger.info(f"Skipping non-URL or non-MD link target: {link_target}")
        
        markdown_urls = processed_markdown_urls
        
        download_tasks = []
        temp_file_paths_map_for_saving = {} # {original_url: local_abs_path} for saving after download

        for md_url in markdown_urls:
            local_md_path_abs = get_local_path_from_url(url_to_llmstxt, md_url, unique_cache_subdir_abs)
            if local_md_path_abs:
                download_tasks.append(download_file(md_url, client))
                temp_file_paths_map_for_saving[md_url] = local_md_path_abs 
            else:
                logger.warning(f"Could not determine local path for {md_url}. Skipping.")

        logger.info(f"Attempting to download {len(download_tasks)} markdown files concurrently...")
        downloaded_contents = await asyncio.gather(*download_tasks, return_exceptions=True)

        files_downloaded_count = 0
        for i, content_or_exc in enumerate(downloaded_contents):
            # This relies on python >=3.7 for dicts preserving insertion order for markdown_urls from processed_markdown_urls
            # A more robust way would be to map tasks to URLs if gather doesn't guarantee order of results matching input tasks.
            # However, asyncio.gather *does* preserve the order of awaitables.
            md_url_key = markdown_urls[i] 
            local_md_path_abs = temp_file_paths_map_for_saving.get(md_url_key)

            if not local_md_path_abs: 
                logger.error(f"Internal error: No local path found for URL {md_url_key} after download. Skipping save.")
                continue

            if isinstance(content_or_exc, Exception) or content_or_exc is None:
                logger.error(f"Failed to download or got empty content for {md_url_key}: {content_or_exc}")
                continue
            
            md_content = content_or_exc
            try:
                os.makedirs(os.path.dirname(local_md_path_abs), exist_ok=True)
                with open(local_md_path_abs, 'w', encoding='utf-8') as f_md:
                    f_md.write(md_content)
                logger.info(f"Saved {md_url_key} to {local_md_path_abs}")
                downloaded_files_path_url_map_for_indexing[local_md_path_abs] = md_url_key # For detailed index generation
                files_downloaded_count += 1
            except Exception as e:
                logger.error(f"Failed to save {md_url_key} to {local_md_path_abs}: {e}", exc_info=True)
        
        logger.info(f"Successfully downloaded and saved {files_downloaded_count} out of {len(markdown_urls)} markdown files.")

        # Generate detailed index for the newly downloaded files
        if downloaded_files_path_url_map_for_indexing:
            generated_detailed_index_path = await generate_detailed_index_async(unique_cache_subdir_abs, downloaded_files_path_url_map_for_indexing)
            if generated_detailed_index_path:
                detailed_index_md_path = generated_detailed_index_path # Use the newly generated one
            else:
                logger.error("Failed to generate detailed index after fresh download. Proceeding without it.")
                detailed_index_md_path = None # Ensure it's None if generation failed
        else:
            logger.info("No files were successfully downloaded and mapped, skipping detailed index generation.")
            detailed_index_md_path = None

        try:
            with open(completion_marker_file, 'w', encoding='utf-8') as f_marker:
                f_marker.write("Download completed successfully.")
            logger.info(f"Created completion marker: {completion_marker_file}")
        except Exception as e:
            logger.error(f"Failed to create completion marker {completion_marker_file}: {e}", exc_info=True)

        # Save the llms-full.txt hash for future cache validation
        save_llms_full_hash(unique_cache_subdir_abs, current_llms_full_hash)

    DOCS_ROOT_PATH_ABS = unique_cache_subdir_abs
    return unique_cache_subdir_abs, main_index_content_str, detailed_index_md_path


def generate_folder_index(current_docs_root_path: str, index_txt_content: str) -> str:
    logger.info(f"Generating ultra-simplified folder index for: {current_docs_root_path}")
    structure = [
        "Available Documentation Files (Simple List):",
        "============================================"
    ]

    found_files = False
    # Ensure files are sorted for consistent output, e.g., by relative path
    all_md_files = []
    for root, _, files in os.walk(current_docs_root_path):
        if not root.startswith(current_docs_root_path): 
            logger.warning(f"generate_folder_index walked out of current_docs_root_path: {root}. Skipping.")
            continue
        for file_name in files:
            if file_name.endswith(".md") and file_name not in ["_index.txt", ".download_complete", "detailed_index.md"]:
                all_md_files.append(os.path.join(root, file_name))
    
    for full_file_path in sorted(all_md_files):
        relative_file_path = os.path.relpath(full_file_path, current_docs_root_path)
        description = "(No description available)"
        try:
            with open(full_file_path, 'r', encoding='utf-8') as f_md:
                first_line = f_md.readline().strip().lstrip('# ').strip()
                if first_line:
                    description = first_line[:100] + ('...' if len(first_line) > 100 else '')
        except Exception as e:
            logger.warning(f"Could not read first line of {relative_file_path}: {e}")
        
        structure.append(f"- FILE: '{relative_file_path}' -- DESCRIPTION: {description}")
        found_files = True
    
    if not found_files:
        structure.append("(No markdown files found in the cache for this documentation source, excluding special files)")
    
    master_content = "\n".join(structure)
    logger.info(f"Generated ultra-simplified master index (length: {len(master_content)} chars). Preview: {master_content[:300]}...")
    return master_content


def read_files(files_to_read: list[str]) -> str:
    """Reads a list of files and returns their content concatenated.
    File paths must be relative to the dynamically configured documentation root path.
    """
    # Determine which documentation source to use
    if CURRENT_ACTIVE_DOC and CURRENT_ACTIVE_DOC in INDEXED_DOCS:
        docs_root_path = INDEXED_DOCS[CURRENT_ACTIVE_DOC]['cache_dir']
        logger.info(f"ADK Tool 'read_files' called with: {files_to_read} against active doc root: {docs_root_path}")
    else:
        docs_root_path = DOCS_ROOT_PATH_ABS
        logger.info(f"ADK Tool 'read_files' called with: {files_to_read} against legacy root: {docs_root_path}")
    
    all_content = []

    if not docs_root_path: 
        logger.error("Documentation root path is not configured. Cannot read files.")
        return "Error: Documentation root path is not configured. Please set up documentation first."

    for file_to_read in files_to_read:
        if not file_to_read:
            logger.warning("Empty file path provided to read_files. Skipping.")
            continue

        if os.path.isabs(file_to_read):
            logger.error(f"Absolute path provided to read_files: {file_to_read}. This is not allowed for security reasons.")
            all_content.append(f"Error: Cannot read absolute path '{file_to_read}' for security reasons.")
            continue

        if ".." in file_to_read.split(os.sep):
            logger.error(f"Path traversal detected in read_files: {file_to_read}. This is not allowed for security reasons.")
            all_content.append(f"Error: Cannot read path '{file_to_read}' containing '..' for security reasons.")
            continue

        full_path = os.path.join(docs_root_path, file_to_read)
        full_path = os.path.normpath(full_path)

        if not full_path.startswith(docs_root_path):
            logger.error(f"Path traversal detected after normalization in read_files: {file_to_read} -> {full_path}. This is not allowed for security reasons.")
            all_content.append(f"Error: Cannot read path '{file_to_read}' due to security restrictions.")
            continue

        if os.path.exists(full_path) and os.path.isfile(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                all_content.append(f"=== File: {file_to_read} ===\n{content}")
                logger.info(f"Successfully read file: {file_to_read}")
            except Exception as e:
                logger.error(f"Failed to read file {file_to_read}: {e}")
                all_content.append(f"Error reading file '{file_to_read}': {e}")
        else:
            logger.warning(f"File not found or not a file: {file_to_read} (full path: {full_path})")
            all_content.append(f"File not found: {file_to_read}")

    result = "\n\n".join(all_content)
    logger.info(f"read_files completed. Total content length: {len(result)} characters")
    return result


def save_indexed_docs_state():
    """Save the current INDEXED_DOCS state to a JSON file for persistence."""
    global INDEXED_DOCS, CURRENT_ACTIVE_DOC
    
    try:
        # Ensure base cache directory exists
        os.makedirs(BASE_CACHE_DIR, exist_ok=True)
        
        state_data = {
            'indexed_docs': INDEXED_DOCS,
            'current_active_doc': CURRENT_ACTIVE_DOC
        }
        
        with open(INDEXED_DOCS_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved indexed docs state to: {INDEXED_DOCS_STATE_FILE}")
        
    except Exception as e:
        logger.error(f"Failed to save indexed docs state: {e}", exc_info=True)


def load_indexed_docs_state():
    """Load the INDEXED_DOCS state from JSON file if it exists."""
    global INDEXED_DOCS, CURRENT_ACTIVE_DOC
    
    try:
        if os.path.exists(INDEXED_DOCS_STATE_FILE):
            with open(INDEXED_DOCS_STATE_FILE, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            # Validate that cache directories still exist
            loaded_docs = {}
            for url, doc_info in state_data.get('indexed_docs', {}).items():
                cache_dir = doc_info.get('cache_dir')
                if cache_dir and os.path.exists(cache_dir):
                    loaded_docs[url] = doc_info
                    logger.info(f"Restored indexed doc: {url} -> {cache_dir}")
                else:
                    logger.warning(f"Skipping indexed doc {url} - cache directory not found: {cache_dir}")
            
            INDEXED_DOCS = loaded_docs
            
            # Validate current active doc
            current_active = state_data.get('current_active_doc')
            if current_active and current_active in INDEXED_DOCS:
                CURRENT_ACTIVE_DOC = current_active
                logger.info(f"Restored active documentation source: {current_active}")
            else:
                CURRENT_ACTIVE_DOC = None
                logger.info("No valid active documentation source found")
            
            logger.info(f"Loaded {len(INDEXED_DOCS)} indexed documentation sources from state file")
            
        else:
            logger.info("No existing indexed docs state file found")
            
    except Exception as e:
        logger.error(f"Failed to load indexed docs state: {e}", exc_info=True)


def discover_existing_cache_directories():
    """Discover existing cache directories and try to restore them to INDEXED_DOCS."""
    global INDEXED_DOCS
    
    try:
        if not os.path.exists(BASE_CACHE_DIR):
            logger.info("Base cache directory does not exist - no existing caches to discover")
            return
        
        discovered_count = 0
        for item in os.listdir(BASE_CACHE_DIR):
            item_path = os.path.join(BASE_CACHE_DIR, item)
            
            # Skip files and look only at directories
            if not os.path.isdir(item_path):
                continue
                
            # Look for URL marker file
            url_marker_file = os.path.join(item_path, ".source_url")
            if os.path.exists(url_marker_file):
                try:
                    with open(url_marker_file, 'r', encoding='utf-8') as f:
                        source_url = f.read().strip()
                    
                    # Skip if already in INDEXED_DOCS
                    if source_url in INDEXED_DOCS:
                        continue
                    
                    # Try to extract project name from llms.txt if available
                    llms_txt_file = os.path.join(item_path, "llms.txt")
                    project_name = "unknown_project"
                    if os.path.exists(llms_txt_file):
                        try:
                            with open(llms_txt_file, 'r', encoding='utf-8') as f:
                                llms_content = f.read()
                            project_name = extract_project_name_from_llmstxt(llms_content)
                        except Exception as e:
                            logger.warning(f"Could not read llms.txt from {llms_txt_file}: {e}")
                    
                    # Try to load detailed index
                    detailed_index_file = os.path.join(item_path, "detailed_index.md")
                    detailed_index_content = "Error: Detailed index not found"
                    if os.path.exists(detailed_index_file):
                        try:
                            with open(detailed_index_file, 'r', encoding='utf-8') as f:
                                detailed_index_content = f.read()
                        except Exception as e:
                            logger.warning(f"Could not read detailed index from {detailed_index_file}: {e}")
                    
                    # Generate master index (simplified version)
                    master_index_content = f"# {project_name} Documentation\n\nDiscovered from cache directory: {item_path}"
                    
                    # Add to INDEXED_DOCS
                    INDEXED_DOCS[source_url] = {
                        'cache_dir': item_path,
                        'project_name': project_name,
                        'detailed_index_content': detailed_index_content,
                        'master_index_content': master_index_content
                    }
                    
                    discovered_count += 1
                    logger.info(f"Discovered existing cache: {source_url} -> {item_path} (Project: {project_name})")
                    
                except Exception as e:
                    logger.warning(f"Error processing cache directory {item_path}: {e}")
        
        if discovered_count > 0:
            logger.info(f"Discovered {discovered_count} existing cache directories")
            # Set the first discovered as active if no active doc is set
            if not CURRENT_ACTIVE_DOC and INDEXED_DOCS:
                CURRENT_ACTIVE_DOC = next(iter(INDEXED_DOCS.keys()))
                logger.info(f"Set first discovered doc as active: {CURRENT_ACTIVE_DOC}")
        else:
            logger.info("No existing cache directories discovered")
            
    except Exception as e:
        logger.error(f"Error during cache directory discovery: {e}", exc_info=True)


# === SCRAPING HELPER FUNCTIONS (adapted from complete_docs_scraper.py) ===

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def sanitize_filename(url_path):
    """Sanitize URL path for use as filename."""
    decoded_path = unquote(url_path)
    sanitized = decoded_path.replace('/', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
    sanitized = sanitized.strip('_ ')
    if not sanitized:
        return "index"
    return sanitized

def get_all_links_from_html(html_content, base_url, subdomain_to_keep):
    """Extract all relevant links from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()
    
    # Find all links
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        
        # Skip empty hrefs, anchors, and javascript links
        if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
            continue
            
        # Convert relative URLs to absolute
        full_url = urljoin(base_url, href)
        parsed_full_url = urlparse(full_url)
        
        # Remove fragment and query parameters for normalization
        normalized_url = parsed_full_url._replace(fragment="", query="").geturl()
        
        # Ensure URL ends without trailing slash for consistency (except root)
        if normalized_url.endswith('/') and normalized_url != subdomain_to_keep.rstrip('/') + '/':
            normalized_url = normalized_url.rstrip('/')
        
        # Check if URL belongs to the target domain/subdomain
        if normalized_url.startswith(subdomain_to_keep.rstrip('/')):
            links.add(normalized_url)
            
    return links

async def scrape_single_page_async(url, subdomain_to_keep_filter, output_folder, timeout=30000):
    """Scrape a single page with async Playwright and improved error handling."""
    start_time = time.time()
    max_retries = 2
    retry_count = 0

    while retry_count <= max_retries:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={'width': 1280, 'height': 720}
                )
                page = await context.new_page()
                
                html_content = None
                actual_url_processed = url 
                
                try:
                    response = await page.goto(url, timeout=timeout, wait_until='domcontentloaded')
                    if response:
                        actual_url_processed = response.url
                    
                    # Wait for dynamic content
                    await page.wait_for_timeout(2000)
                    html_content = await page.content()
                    
                except Exception as e:
                    logger.warning(f"Attempt {retry_count + 1}: Error loading {url}: {e}")
                    if retry_count < max_retries:
                        retry_count += 1
                        await browser.close()
                        await asyncio.sleep(1)
                        continue
                    else:
                        await browser.close()
                        return None
                
                await browser.close()
                break

        except Exception as e:
            logger.error(f"Browser error for {url}: {e}")
            if retry_count < max_retries:
                retry_count += 1
                await asyncio.sleep(1)
                continue
            else:
                return None

    if not html_content:
        logger.warning(f"Failed to get content from {url} after {max_retries + 1} attempts.")
        return None

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        title_tag = soup.find('title')
        page_title = title_tag.string.strip() if title_tag else urlparse(actual_url_processed).path.split('/')[-1] or "Untitled"
        page_title = page_title.replace('\n', '').replace('\r', '')

        # Skip error pages
        if any(indicator in page_title.lower() for indicator in ['page not found', '404', 'error', 'not found']):
            logger.info(f"Skipping error page: {actual_url_processed} (Title: {page_title})")
            return None

        # Try multiple content selectors in order of preference
        main_content_tags = [
            'main', 
            'article', 
            '[role="main"]',
            '.content', 
            '.main-content', 
            '.post-content',
            '.documentation',
            '.docs-content',
            '#content',
            '.markdown-body',
            'body'
        ]
        
        content_element = None
        for tag_or_class in main_content_tags:
            if tag_or_class.startswith('.'):
                content_element = soup.find(attrs={"class": tag_or_class[1:]})
            elif tag_or_class.startswith('#'):
                content_element = soup.find(attrs={"id": tag_or_class[1:]})
            elif tag_or_class.startswith('['):
                if 'role="main"' in tag_or_class:
                    content_element = soup.find(attrs={"role": "main"})
            else:
                content_element = soup.find(tag_or_class)
            if content_element:
                break
        
        if not content_element:
            logger.warning(f"No suitable content element found for {actual_url_processed}")
            return None

        # Remove unwanted elements
        for unwanted in content_element.find_all(['script', 'style', 'nav', 'header', 'footer', '.sidebar', '.navigation']):
            unwanted.decompose()

        markdown_content = md(str(content_element), heading_style="atx", bullets="-")
        
        # Clean up markdown
        lines = markdown_content.split('\n')
        cleaned_lines = []
        for line in lines:
            if not cleaned_lines and not line.strip():
                continue
            cleaned_lines.append(line)
        
        markdown_content = '\n'.join(cleaned_lines).strip()
        
        # Skip pages with minimal content
        if len(markdown_content) < 50:
            logger.info(f"Skipping page with minimal content: {actual_url_processed}")
            return None
        
        # Create folder structure based on URL path with improved filename generation
        parsed_actual_url = urlparse(actual_url_processed)
        url_path = parsed_actual_url.path.strip('/')
        
        if url_path:
            path_parts = url_path.split('/')
            folder_path = os.path.join(output_folder, *path_parts[:-1]) if len(path_parts) > 1 else output_folder
            base_filename = sanitize_filename(path_parts[-1]) if path_parts[-1] else "index"
        else:
            folder_path = output_folder
            base_filename = "index"
        
        # Ensure unique filenames to prevent overwrites
        os.makedirs(folder_path, exist_ok=True)
        saved_filepath = os.path.join(folder_path, f"{base_filename}.md")
        
        # If file already exists, add a suffix
        counter = 1
        original_filepath = saved_filepath
        while os.path.exists(saved_filepath):
            name_without_ext = os.path.splitext(original_filepath)[0]
            saved_filepath = f"{name_without_ext}_{counter}.md"
            counter += 1

        # Create markdown with metadata
        final_markdown = f"# {page_title}\n\nSource: {actual_url_processed}\n\n{markdown_content}"

        with open(saved_filepath, 'w', encoding='utf-8') as f:
            f.write(final_markdown)
        
        # Extract new links
        links_on_page = get_all_links_from_html(html_content, actual_url_processed, subdomain_to_keep_filter)
        
        end_time = time.time()
        
        return {
            'url': url,
            'actual_url': actual_url_processed,
            'title': page_title,
            'content': final_markdown,
            'file_path': saved_filepath,
            'links': links_on_page,
            'processing_time': end_time - start_time
        }

    except Exception as e:
        logger.error(f"Content processing error for {url}: {e}")
        return None

async def generate_llms_txt_from_scraped_files(scraped_files_meta, output_folder):
    """Generate llms.txt file in mem0 format from scraped files."""
    llms_file_path = os.path.join(output_folder, "llms.txt")
    
    # Group files by folder structure
    grouped_files = {}
    
    for result in scraped_files_meta.values():
        if not result or not result.get('title') or not result.get('actual_url'):
            continue
            
        title = result['title']
        
        # Skip error pages
        if any(indicator in title.lower() for indicator in ['page not found', '404', 'error']):
            continue
                
        # Extract relative path from the saved file path
        rel_path = os.path.relpath(result['file_path'], output_folder)
        folder = os.path.dirname(rel_path)
        
        if folder == '.':
            folder = 'Root'
        
        if folder not in grouped_files:
            grouped_files[folder] = []
        
        # Clean title for display
        clean_title = title.replace('[', '').replace(']', '').strip()
        # Remove site suffix if present
        clean_title = re.sub(r'\s*\|\s*.*$', '', clean_title)
        
        grouped_files[folder].append((clean_title, result['actual_url']))
    
    # Remove duplicates within each folder
    for folder in grouped_files:
        seen_urls = set()
        unique_files = []
        for title, url in grouped_files[folder]:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_files.append((title, url))
        grouped_files[folder] = unique_files
    
    # Write the llms.txt file
    with open(llms_file_path, 'w', encoding='utf-8') as f:
        f.write("# Documentation\n\n")
        
        # Sort folders for consistent output
        for folder in sorted(grouped_files.keys()):
            if folder == 'Root':
                f.write("## Docs\n\n")
            else:
                folder_name = folder.replace('_', ' ').replace('-', ' ').title()
                f.write(f"## {folder_name}\n\n")
            
            # Sort files within folder
            for title, url in sorted(grouped_files[folder]):
                f.write(f"- [{title}]({url})\n")
            
            f.write("\n")
        
        # Add optional section
        f.write(f"## Optional\n\n")
        if scraped_files_meta:
            first_result = next(iter(scraped_files_meta.values()))
            if first_result and first_result.get('actual_url'):
                base_url = f"{urlparse(first_result['actual_url']).scheme}://{urlparse(first_result['actual_url']).netloc}"
                f.write(f"- [Documentation Home]({base_url})\n")
    
    logger.info(f"✅ Generated llms.txt at: {llms_file_path}")
    return llms_file_path

async def generate_llms_full_txt_from_scraped_files(scraped_files_meta, output_folder):
    """Generate llms-full.txt with concatenated content from scraped files."""
    llms_full_path = os.path.join(output_folder, "llms-full.txt")
    
    all_content = []
    
    # Sort by URL for consistent ordering
    sorted_results = sorted(scraped_files_meta.values(), key=lambda x: x['actual_url'] if x else "")
    
    for result in sorted_results:
        if not result or not result.get('content'):
            continue
            
        content = result['content']
        url = result['actual_url']
        
        # Extract title and content from the markdown
        lines = content.splitlines()
        if not lines:
            continue

        # Extract title (first line, removing '# ')
        title = lines[0].strip().lstrip('# ').strip()
        
        # Find content after metadata
        content_start_index = 0
        for i, line in enumerate(lines):
            if line.strip().lower().startswith("source:"):
                content_start_index = i + 1
                break
        
        # Skip blank lines
        while content_start_index < len(lines) and not lines[content_start_index].strip():
            content_start_index += 1
            
        actual_content = "\n".join(lines[content_start_index:]).strip()

        # Append to collection
        all_content.append(f"URL: {url}\nPage Name: {title}\n\n{actual_content}\n\n---\n")

    concatenated_content = "\n".join(all_content)
    
    # Write to file
    with open(llms_full_path, 'w', encoding='utf-8') as f:
        f.write(concatenated_content)
    
    logger.info(f"✅ Generated llms-full.txt at: {llms_full_path}")
    return llms_full_path

async def scrape_documentation_site(start_url, subdomain_to_keep=None, max_workers=8, max_urls=500, timeout=30000):
    """
    Scrape a complete documentation site and return scraped files metadata.
    This is the main scraping orchestrator function - improved with ThreadPoolExecutor approach.
    """
    start_url = start_url.rstrip('/')
    if not subdomain_to_keep:
        subdomain_to_keep = start_url
    
    # Ensure subdomain_to_keep ends with /
    parsed_s_to_keep = urlparse(subdomain_to_keep)
    if not subdomain_to_keep.endswith('/') and (not parsed_s_to_keep.path or parsed_s_to_keep.path.endswith('/') or '.' not in parsed_s_to_keep.path.split('/')[-1]):
        subdomain_to_keep += '/'
    
    logger.info(f"🚀 Starting documentation scraping")
    logger.info(f"📍 Start URL: {start_url}")
    logger.info(f"🎯 Keep URLs matching: {subdomain_to_keep}")
    logger.info(f"👥 Max workers: {max_workers}")
    logger.info(f"🔢 Max URLs: {max_urls}")
    logger.info(f"⏱️  Timeout: {timeout}ms")
    
    def normalize_url(url):
        """Normalize URL for consistent comparison and deduplication."""
        parsed = urlparse(url)
        # Remove fragment and query parameters
        normalized = parsed._replace(fragment="", query="").geturl()
        # Remove trailing slash except for domain root to avoid duplicates
        if normalized.endswith('/') and normalized.count('/') > 2:
            normalized = normalized.rstrip('/')
        return normalized
    
    overall_start_time = time.time()
    master_visited_urls = set()       
    master_to_visit_urls_q = {start_url}
    all_scraped_results = {}     
    urls_processed_count = 0
    successful_scrapes = 0
    failed_scrapes = 0
    
    logger.info("🔍 Discovering and scraping pages...")
    
    # Create a temporary output folder for scraping
    temp_output_folder = f"/tmp/scrape_{int(time.time())}"
    os.makedirs(temp_output_folder, exist_ok=True)
    
    # Use ThreadPoolExecutor for better parallelization like complete_docs_scraper.py
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url_map = {}
        
        while (master_to_visit_urls_q or future_to_url_map) and urls_processed_count < max_urls:
            # Submit new tasks dynamically
            while (master_to_visit_urls_q and 
                   len(future_to_url_map) < max_workers and 
                   urls_processed_count < max_urls):
                
                current_url_to_fetch = master_to_visit_urls_q.pop()
                normalized_url = normalize_url(current_url_to_fetch)

                if normalized_url in master_visited_urls:
                    continue 

                master_visited_urls.add(normalized_url) 
                urls_processed_count += 1
                logger.info(f"[{time.time() - overall_start_time:.1f}s] 📤 Submitting ({urls_processed_count}/{max_urls}): {normalized_url}")
                
                # Create asyncio task wrapped in executor for thread pool
                future = executor.submit(
                    asyncio.run,
                    scrape_single_page_async(normalized_url, subdomain_to_keep, temp_output_folder, timeout)
                )
                future_to_url_map[future] = normalized_url

            if not future_to_url_map:
                if not master_to_visit_urls_q: 
                    break 
                await asyncio.sleep(0.1)  # Small async delay
                continue

            # Process completed tasks as they finish
            done_futures = []
            for future in future_to_url_map:
                if future.done():
                    done_futures.append(future)
            
            for future in done_futures:
                original_submitted_url = future_to_url_map.pop(future)
                try:
                    result = future.result()

                    if result:
                        successful_scrapes += 1
                        logger.info(f"[{time.time() - overall_start_time:.1f}s] ✅ SUCCESS: {result['actual_url']} -> {os.path.relpath(result['file_path'], temp_output_folder)} ({result['processing_time']:.1f}s)")
                        all_scraped_results[original_submitted_url] = result
                        
                        # Add new discovered links to queue immediately
                        for link in result['links']:
                            norm_link = normalize_url(link)
                            if (norm_link.startswith(subdomain_to_keep.rstrip('/')) and 
                                norm_link not in master_visited_urls and 
                                norm_link not in master_to_visit_urls_q):
                                master_to_visit_urls_q.add(norm_link)
                                logger.debug(f"🔗 Added new link to queue: {norm_link}")
                    else:
                        failed_scrapes += 1
                        logger.warning(f"[{time.time() - overall_start_time:.1f}s] ❌ FAILED: {original_submitted_url}")
                        
                except Exception as exc:
                    failed_scrapes += 1
                    logger.error(f"[{time.time() - overall_start_time:.1f}s] ❌ EXCEPTION for {original_submitted_url}: {exc}")
            
            # Small delay to prevent busy waiting
            if future_to_url_map:
                await asyncio.sleep(0.1)
    
    overall_end_time = time.time()
    
    logger.info("📊 Scraping Results:")
    logger.info(f"⏱️  Total time: {overall_end_time - overall_start_time:.1f} seconds")
    logger.info(f"🔢 URLs processed: {len(master_visited_urls)}")
    logger.info(f"✅ Successful: {successful_scrapes}")
    logger.info(f"❌ Failed: {failed_scrapes}")
    logger.info(f"📈 Success rate: {successful_scrapes / max(urls_processed_count, 1) * 100:.1f}%")
    
    return all_scraped_results, temp_output_folder

# === END SCRAPING HELPER FUNCTIONS ===

@mcp_server.tool()
async def ask_doc_agent(query: str) -> str:
    logging.info(f"MCP Tool 'ask_doc_agent' called with query: {query[:100]}...")
    try:
        # Use CURRENT_ACTIVE_DOC if set, otherwise fall back to legacy globals
        if CURRENT_ACTIVE_DOC and CURRENT_ACTIVE_DOC in INDEXED_DOCS:
            active_doc = INDEXED_DOCS[CURRENT_ACTIVE_DOC]
            docs_root_path = active_doc['cache_dir']
            detailed_index_content = active_doc['detailed_index_content']
            logger.info(f"Using active documentation source: {CURRENT_ACTIVE_DOC}")
        else:
            # Fall back to legacy globals for backward compatibility
            docs_root_path = DOCS_ROOT_PATH_ABS
            detailed_index_content = DETAILED_INDEX_CONTENT
            logger.info("Using legacy global documentation source")

        if not docs_root_path or detailed_index_content is None:
            err_msg = "ask_doc_agent: Documentation source not fully initialized. Critical context is missing."
            logging.error(err_msg)
            return f"ERROR: {err_msg}"

        session_service = InMemorySessionService()
        app_name = "doc_agent_mcp_app_v3" 

        gemini_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            logging.error("ask_doc_agent: GOOGLE_API_KEY or GEMINI_API_KEY not found for main agent.")
            return "ERROR: Gemini API key not configured on server for the documentation agent."
        os.environ["GOOGLE_API_KEY"] = gemini_api_key 

        # Pass detailed_index_content and docs_root_path to the agent configuration
        doc_agent = await get_documentation_query_agent_async(detailed_index_content, docs_root_path)
        logging.info(f"ask_doc_agent: Documentation agent '{doc_agent.name}' created/retrieved using detailed index.")

        runner = Runner(
            app_name=app_name,
            agent=doc_agent,
            session_service=session_service,
        )
        logging.info(f"ask_doc_agent: Runner created for app '{app_name}'.")

        session = await session_service.create_session(
            state={},
            app_name=app_name,
            user_id="doc_agent_user_v3" 
        )
        logging.info(f"ask_doc_agent: Session created with ID: {session.id} for app '{app_name}'.")
        
        result_parts = []
        logger.info(f"ask_doc_agent: Calling runner.run_async with session_id: {session.id}")
        
        async for event in runner.run_async(
            session_id=session.id,
            user_id="doc_agent_user_v3",
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=query)]
            )
        ):
            logging.debug(f"ask_doc_agent: Event received: {event}")
            if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        result_parts.append(part.text)
                        logging.info(f"ask_doc_agent: Agent text response part: {part.text[:200]}...")
                    elif hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        logging.info(f"ask_doc_agent: Agent requested function call: {fc.name} with args: {fc.args}")
                    elif hasattr(part, 'function_response') and part.function_response:
                        fr = part.function_response
                        logging.info(f"ask_doc_agent: Agent received function response for {fr.name}: {str(fr.response)[:200]}...")
        
        final_response = "".join(result_parts)
        logging.info(f"ask_doc_agent: Final agent response: {final_response[:300]}...")
        
        return final_response if final_response else "Agent did not produce a textual response."

    except Exception as e:
        logging.error(f"Error during ask_doc_agent: {e}", exc_info=True)
        error_details = str(e)
        if hasattr(e, 'details') and callable(e.details):
            try: error_details += f" - Details: {e.details()}"
            except: pass 
        elif hasattr(e, 'args') and e.args: error_details += f" - Args: {e.args}"
        return f"ERROR: An unexpected error occurred in ask_doc_agent: {error_details}"


async def get_documentation_query_agent_async(current_detailed_index_content: str, docs_root_path: str) -> LlmAgent:
    """Helper to configure and return the documentation LlmAgent, now using detailed index."""
    read_files_adk_tool = FunctionTool(read_files)
    logger.info(f"Created ADK tool for 'read_files'. Agent will use DOCS_ROOT_PATH_ABS: {docs_root_path}")

    agent_instruction_template = """You are a highly intelligent Documentation Assistant.
Your primary task is to answer user questions based on the "DETAILED Documentation Index" provided below.
This index contains a list of available markdown files, their original URLs, main topics, major sections, and a summary for each.

To answer a question, you MUST follow these steps:
1.  Carefully analyze the user's query for keywords, topics, and specific details they are asking about.
2.  Thoroughly review the "DETAILED Documentation Index" below. For each file entry (which includes its path, URL, summary, topics, and sections), assess its relevance to the user's query. Pay close attention to the summaries and listed topics/sections.
3.  Identify the TOP 1-3 MOST RELEVANT file(s) based on this detailed comparison.
4.  You MUST use the 'read_files' tool to read the content of these most relevant file(s). Provide the exact relative file paths as listed in the index (e.g., 'path/to/file1.md').
5.  After reading the file(s) using the tool, formulate your answer based *only* on the content you have read from those specific files and the information in the detailed index.
6.  If, after reviewing the detailed index, no file appears sufficiently relevant, or if after reading relevant files you still cannot find the answer, then state that you could not find the information in the provided documents.
7.  When providing an answer, if possible, cite the source file(s) you used (e.g., "According to 'path/to/file.md', ...").

Do not invent information. Your knowledge is strictly limited to the documents you read via the 'read_files' tool and the provided DETAILED Documentation Index.
Do not attempt to access external URLs or browse the web.

DETAILED Documentation Index:
=============================
{knowledge_base_placeholder}
"""
    agent_instruction = agent_instruction_template.format(
        knowledge_base_placeholder=current_detailed_index_content
    )
    logger.info("Attempting to create LlmAgent for documentation queries with detailed index.")
    return LlmAgent(
        name="documentation_query_agent_v3", 
        instruction=agent_instruction,
        tools=[read_files_adk_tool],
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-pro-preview-03-25")
    )

@mcp_server.tool()
async def test_basic_functionality() -> str:
    """Test basic functionality to debug indexing issues"""
    try:
        import httpx
        import os
        
        # Test 1: Basic imports
        result = ["=== Basic Functionality Test ==="]
        result.append(f"httpx imported successfully: {httpx.__version__}")
        result.append(f"Current working directory: {os.getcwd()}")
        result.append(f"BASE_CACHE_DIR: {BASE_CACHE_DIR}")
        result.append(f"BASE_CACHE_DIR exists: {os.path.exists(BASE_CACHE_DIR)}")
        
        # Test 2: Try creating httpx client
        try:
            async with httpx.AsyncClient() as client:
                result.append("httpx AsyncClient creation: SUCCESS")
        except Exception as e:
            result.append(f"httpx AsyncClient creation: FAILED - {e}")
        
        # Test 3: Try simple HTTP request
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://httpbin.org/get", timeout=10)
                result.append(f"Simple HTTP request: SUCCESS (status {response.status_code})")
        except Exception as e:
            result.append(f"Simple HTTP request: FAILED - {e}")
        
        # Test 4: Test OpenAI API key
        openai_key = os.getenv("OPENAI_API_KEY")
        result.append(f"OPENAI_API_KEY present: {bool(openai_key)}")
        if openai_key:
            result.append(f"OPENAI_API_KEY length: {len(openai_key)}")
        
        return "\n".join(result)
        
    except Exception as e:
        import traceback
        return f"ERROR in test_basic_functionality: {e}\nTraceback: {traceback.format_exc()}"


@mcp_server.tool()
async def index_documentation(url: str) -> str:
    """Index a new documentation source from a URL containing llms.txt"""
    global INDEXED_DOCS, CURRENT_ACTIVE_DOC
    
    logging.info(f"MCP Tool 'index_documentation' called with URL: {url}")
    
    try:
        # Setup documentation source
        logging.info(f"Calling setup_documentation_source for {url}")
        local_docs_root, index_file_content, detailed_index_file_abs_path = await setup_documentation_source(url)
        logging.info(f"setup_documentation_source returned: root={local_docs_root}, content_len={len(index_file_content) if index_file_content else 'None'}, detailed_path={detailed_index_file_abs_path}")
        
        if not local_docs_root or index_file_content is None:
            error_msg = f"Failed to setup documentation source from {url}"
            logging.error(error_msg)
            return f"ERROR: {error_msg}"
        
        # Generate master index
        master_index_content = generate_folder_index(local_docs_root, index_file_content)
        
        # Load detailed index content
        detailed_index_content = None
        if detailed_index_file_abs_path and os.path.exists(detailed_index_file_abs_path):
            try:
                with open(detailed_index_file_abs_path, 'r', encoding='utf-8') as f_detailed:
                    detailed_index_content = f_detailed.read()
                logger.info(f"Successfully loaded detailed index content from: {detailed_index_file_abs_path}")
            except Exception as e:
                logger.error(f"Failed to read detailed index file {detailed_index_file_abs_path}: {e}")
                detailed_index_content = "Error: Detailed index file was found but could not be read by the server."
        else:
            logger.error(f"Detailed index file not found at: {detailed_index_file_abs_path}")
            detailed_index_content = "Error: Detailed index was not generated or found by the server."
        
        # Extract project name for reference
        project_name = extract_project_name_from_llmstxt(index_file_content)
        
        # Store in indexed docs
        INDEXED_DOCS[url] = {
            'cache_dir': local_docs_root,
            'project_name': project_name,
            'detailed_index_content': detailed_index_content,
            'master_index_content': master_index_content
        }
        
        # Set as current active doc
        CURRENT_ACTIVE_DOC = url
        
        # Save state for persistence
        save_indexed_docs_state()
        
        success_msg = f"Successfully indexed documentation from {url}. Project: '{project_name}'. Cache directory: {local_docs_root}. Set as active documentation source."
        logging.info(success_msg)
        return success_msg
        
    except Exception as e:
        error_msg = f"Error during index_documentation for {url}: {e}"
        logging.error(error_msg, exc_info=True)
        # Return more detailed error information
        import traceback
        traceback_str = traceback.format_exc()
        logging.error(f"Full traceback: {traceback_str}")
        return f"ERROR: {error_msg}\nDetails: {str(e)}\nType: {type(e).__name__}"


@mcp_server.tool()
async def list_documentation_sources() -> str:
    """List all indexed documentation sources"""
    global INDEXED_DOCS, CURRENT_ACTIVE_DOC
    
    logging.info("MCP Tool 'list_documentation_sources' called")
    
    if not INDEXED_DOCS:
        return "No documentation sources have been indexed yet. Use 'index_documentation' to add sources."
    
    result_lines = ["Indexed Documentation Sources:"]
    result_lines.append("=" * 40)
    
    for url, doc_info in INDEXED_DOCS.items():
        status = " (ACTIVE)" if url == CURRENT_ACTIVE_DOC else ""
        result_lines.append(f"• URL: {url}{status}")
        result_lines.append(f"  Project: {doc_info['project_name']}")
        result_lines.append(f"  Cache: {doc_info['cache_dir']}")
        result_lines.append("")
    
    return "\n".join(result_lines)


@mcp_server.tool()
async def set_active_documentation(url: str) -> str:
    """Set the active documentation source for queries"""
    global INDEXED_DOCS, CURRENT_ACTIVE_DOC
    
    logging.info(f"MCP Tool 'set_active_documentation' called with URL: {url}")
    
    if url not in INDEXED_DOCS:
        available_urls = ", ".join(INDEXED_DOCS.keys()) if INDEXED_DOCS else "None"
        return f"ERROR: Documentation source '{url}' not found. Available sources: {available_urls}"
    
    CURRENT_ACTIVE_DOC = url
    project_name = INDEXED_DOCS[url]['project_name']
    
    # Save state for persistence
    save_indexed_docs_state()
    
    success_msg = f"Set active documentation source to: {url} (Project: '{project_name}')"
    logging.info(success_msg)
    return success_msg


@mcp_server.tool()
async def scrape_and_index_documentation(start_url: str, keep_url_pattern: str = None, max_pages: int = 100, max_workers: int = 10) -> str:
    """
    Scrape a documentation website and index it for querying.
    This tool is for websites that don't provide llms.txt files.
    
    Args:
        start_url: The starting URL to begin scraping from
        keep_url_pattern: URL pattern to restrict scraping to (defaults to same domain/path as start_url)
        max_pages: Maximum number of pages to scrape (default: 100, max: 500)
        max_workers: Number of parallel workers for scraping (default: 10, adjust based on your machine)
    """
    global INDEXED_DOCS, CURRENT_ACTIVE_DOC
    
    logging.info(f"MCP Tool 'scrape_and_index_documentation' called with start_url: {start_url}, keep_pattern: {keep_url_pattern}, max_pages: {max_pages}, max_workers: {max_workers}")
    
    try:
        # Validate and sanitize inputs
        if not start_url or not start_url.startswith(('http://', 'https://')):
            return "ERROR: Invalid start_url. Must be a valid HTTP/HTTPS URL."
        
        if max_pages < 1:
            max_pages = 1
        elif max_pages > 500:
            max_pages = 500
            logging.warning(f"max_pages capped at 500 for performance reasons")
        
        if max_workers < 1:
            max_workers = 1
        elif max_workers > 50:
            max_workers = 50
            logging.warning(f"max_workers capped at 50 for performance and safety reasons")
        
        # Use start_url as the identifier for this documentation source
        source_identifier = start_url
        
        # Check if this URL is already indexed
        if source_identifier in INDEXED_DOCS:
            logging.info(f"Documentation source {source_identifier} is already indexed. Skipping scraping.")
            return f"Documentation source already indexed: {source_identifier}. Use 'set_active_documentation' to switch to it."
        
        # Perform the scraping
        logging.info(f"Starting scraping process for {start_url}")
        scraped_files_meta, temp_output_folder = await scrape_documentation_site(
            start_url=start_url,
            subdomain_to_keep=keep_url_pattern,
            max_workers=max_workers,  # Use configurable workers
            max_urls=max_pages,
            timeout=30000
        )
        
        if not scraped_files_meta:
            return f"ERROR: No pages were successfully scraped from {start_url}. Please check the URL and try again."
        
        if not temp_output_folder or not os.path.exists(temp_output_folder):
            return f"ERROR: Scraping completed but output folder is missing. Please try again."
        
        logging.info(f"Scraping completed: {len(scraped_files_meta)} pages scraped to {temp_output_folder}")
        
        # Generate llms.txt and llms-full.txt from scraped files
        logging.info("Generating llms.txt from scraped files...")
        llms_txt_path = await generate_llms_txt_from_scraped_files(scraped_files_meta, temp_output_folder)
        
        logging.info("Generating llms-full.txt from scraped files...")
        llms_full_txt_path = await generate_llms_full_txt_from_scraped_files(scraped_files_meta, temp_output_folder)
        
        # Read the generated llms.txt content
        try:
            with open(llms_txt_path, 'r', encoding='utf-8') as f:
                llms_txt_content = f.read()
        except Exception as e:
            return f"ERROR: Failed to read generated llms.txt: {e}"
        
        # Extract project name and create final cache directory
        project_name = extract_project_name_from_llmstxt(llms_txt_content)
        unique_cache_dir_name = get_unique_cache_dir_name(project_name, source_identifier)
        final_cache_dir = os.path.join(BASE_CACHE_DIR, unique_cache_dir_name)
        
        # Move scraped files to final cache location
        try:
            if os.path.exists(final_cache_dir):
                import shutil
                shutil.rmtree(final_cache_dir)
            
            import shutil
            shutil.move(temp_output_folder, final_cache_dir)
            logging.info(f"Moved scraped files from {temp_output_folder} to {final_cache_dir}")
        except Exception as e:
            return f"ERROR: Failed to move scraped files to cache directory: {e}"
        
        # Create URL marker file to track source
        create_url_marker_file(final_cache_dir, source_identifier)
        
        # Compute hash of llms-full.txt for cache validation
        try:
            with open(os.path.join(final_cache_dir, "llms-full.txt"), 'r', encoding='utf-8') as f:
                llms_full_content = f.read()
            current_hash = compute_content_hash(llms_full_content)
            save_llms_full_hash(final_cache_dir, current_hash)
        except Exception as e:
            logging.warning(f"Failed to save llms-full.txt hash: {e}")
        
        # Build file mapping for detailed index generation
        # This uses the same pattern as the existing setup_documentation_source function
        downloaded_files_path_url_map_for_indexing = {}
        for result in scraped_files_meta.values():
            if result and result.get('file_path') and result.get('actual_url'):
                # Update file path to reflect new location
                old_path = result['file_path']
                relative_path = os.path.relpath(old_path, temp_output_folder)
                new_path = os.path.join(final_cache_dir, relative_path)
                if os.path.exists(new_path):
                    downloaded_files_path_url_map_for_indexing[new_path] = result['actual_url']
        
        # Generate detailed index using the existing logic
        logging.info(f"Generating detailed index for {len(downloaded_files_path_url_map_for_indexing)} scraped files...")
        detailed_index_path = await generate_detailed_index_async(final_cache_dir, downloaded_files_path_url_map_for_indexing)
        
        if not detailed_index_path:
            logging.error("Failed to generate detailed index for scraped documentation")
            detailed_index_content = "Error: Detailed index generation failed after scraping"
        else:
            try:
                with open(detailed_index_path, 'r', encoding='utf-8') as f:
                    detailed_index_content = f.read()
                logging.info(f"Successfully loaded detailed index content from: {detailed_index_path}")
            except Exception as e:
                logging.error(f"Failed to read detailed index file {detailed_index_path}: {e}")
                detailed_index_content = "Error: Detailed index file was generated but could not be read"
        
        # Generate master index (simplified version)
        master_index_content = generate_folder_index(final_cache_dir, llms_txt_content)
        
        # Store in indexed docs
        INDEXED_DOCS[source_identifier] = {
            'cache_dir': final_cache_dir,
            'project_name': project_name,
            'detailed_index_content': detailed_index_content,
            'master_index_content': master_index_content
        }
        
        # Set as current active doc
        CURRENT_ACTIVE_DOC = source_identifier
        
        # Create completion marker
        try:
            completion_marker_file = os.path.join(final_cache_dir, ".download_complete")
            with open(completion_marker_file, 'w', encoding='utf-8') as f:
                f.write("Scraping and indexing completed successfully.")
            logging.info(f"Created completion marker: {completion_marker_file}")
        except Exception as e:
            logging.warning(f"Failed to create completion marker: {e}")
        
        # Save state for persistence
        save_indexed_docs_state()
        
        success_msg = f"Successfully scraped and indexed documentation from {start_url}. Project: '{project_name}'. Scraped {len(scraped_files_meta)} pages. Cache directory: {final_cache_dir}. Set as active documentation source."
        logging.info(success_msg)
        return success_msg
        
    except Exception as e:
        error_msg = f"Error during scrape_and_index_documentation for {start_url}: {e}"
        logging.error(error_msg, exc_info=True)
        # Return more detailed error information
        import traceback
        traceback_str = traceback.format_exc()
        logging.error(f"Full traceback: {traceback_str}")
        return f"ERROR: {error_msg}\nDetails: {str(e)}\nType: {type(e).__name__}"

async def main_async():
    global DOCS_ROOT_PATH_ABS, MASTER_INDEX_CONTENT, DETAILED_INDEX_CONTENT, INDEXED_DOCS, CURRENT_ACTIVE_DOC

    # Check for OpenAI API Key (needed for V3 detailed index generation)
    openai_api_key_env = os.getenv("OPENAI_API_KEY")
    if not openai_api_key_env:
        logger.warning("CRITICAL: OPENAI_API_KEY environment variable not set. Detailed index generation (V3 feature) will fail or be skipped.")
        # Depending on strictness, you might sys.exit(1) here if V3 is mandatory.
        # For now, we'll let it proceed and handle errors in generate_detailed_index_async.
    else:
        logger.info("OPENAI_API_KEY found. Detailed index generation enabled.")

    # Load existing state and discover cache directories first
    logger.info("Loading existing documentation state...")
    load_indexed_docs_state()
    discover_existing_cache_directories()
    
    if INDEXED_DOCS:
        logger.info(f"Found {len(INDEXED_DOCS)} existing documentation sources:")
        for url, doc_info in INDEXED_DOCS.items():
            active_marker = " (ACTIVE)" if url == CURRENT_ACTIVE_DOC else ""
            logger.info(f"  - {doc_info['project_name']}: {url}{active_marker}")

    url_to_llmstxt_env = os.getenv("URL_TO_LLMSTXT")
    if url_to_llmstxt_env:
        logger.info(f"Documentation Agent MCP Server V3 starting with initial URL_TO_LLMSTXT='{url_to_llmstxt_env}'")

        # Check if this URL is already indexed
        if url_to_llmstxt_env in INDEXED_DOCS:
            logger.info(f"Initial URL {url_to_llmstxt_env} is already indexed. Using existing cache.")
            # Set up legacy globals from existing indexed docs
            doc_info = INDEXED_DOCS[url_to_llmstxt_env]
            DOCS_ROOT_PATH_ABS = doc_info['cache_dir']
            MASTER_INDEX_CONTENT = doc_info['master_index_content']
            DETAILED_INDEX_CONTENT = doc_info['detailed_index_content']
            CURRENT_ACTIVE_DOC = url_to_llmstxt_env
            save_indexed_docs_state()  # Save the updated active doc
        else:
            # Setup new documentation source
            local_docs_root, index_file_content, detailed_index_file_abs_path = await setup_documentation_source(url_to_llmstxt_env)

            if not local_docs_root or index_file_content is None: 
                logger.error(f"Failed to setup initial documentation source from {url_to_llmstxt_env}. Server will start without initial documentation.")
            else:
                # Set up legacy globals for backward compatibility
                DOCS_ROOT_PATH_ABS = local_docs_root
                MASTER_INDEX_CONTENT = generate_folder_index(local_docs_root, index_file_content)
                
                # Load detailed index content
                if detailed_index_file_abs_path and os.path.exists(detailed_index_file_abs_path):
                    try:
                        with open(detailed_index_file_abs_path, 'r', encoding='utf-8') as f_detailed:
                            DETAILED_INDEX_CONTENT = f_detailed.read()
                        logger.info(f"Successfully loaded detailed index content from: {detailed_index_file_abs_path}")
                    except Exception as e:
                        logger.error(f"Failed to read detailed index file {detailed_index_file_abs_path}: {e}")
                        DETAILED_INDEX_CONTENT = "Error: Detailed index file was found but could not be read by the server."
                else:
                    logger.error(f"Detailed index file not found at: {detailed_index_file_abs_path}")
                    DETAILED_INDEX_CONTENT = "Error: Detailed index was not generated or found by the server."

                # Also add to the new indexed docs system
                project_name = extract_project_name_from_llmstxt(index_file_content)
                INDEXED_DOCS[url_to_llmstxt_env] = {
                    'cache_dir': local_docs_root,
                    'project_name': project_name,
                    'detailed_index_content': DETAILED_INDEX_CONTENT,
                    'master_index_content': MASTER_INDEX_CONTENT
                }
                CURRENT_ACTIVE_DOC = url_to_llmstxt_env
                save_indexed_docs_state()  # Save the new state
                logger.info(f"Initial documentation source added to indexed docs: {url_to_llmstxt_env}")
    else:
        logger.info("No initial URL_TO_LLMSTXT provided. Server will start with no documentation sources. Use 'index_documentation' tool to add sources.")

    logger.info("Documentation Agent MCP Server V3 initialization complete. Starting MCP server...")
    # MCP server run is handled in synchronous main block

if __name__ == "__main__":
    asyncio.run(main_async()) 

    # Check if we have any documentation sources (either legacy or new system)
    has_docs = (DOCS_ROOT_PATH_ABS and DETAILED_INDEX_CONTENT) or bool(INDEXED_DOCS)
    
    if has_docs:
        logger.info(f"Starting MCP server with documentation sources. Legacy: {bool(DOCS_ROOT_PATH_ABS)}, Indexed: {len(INDEXED_DOCS)}")
        try:
            mcp_server.run() 
            logger.info("mcp_server.run() completed (this is unexpected for a stdio server that should run indefinitely).")
        except KeyboardInterrupt:
            logger.info("MCP Server shutting down due to KeyboardInterrupt.")
        except Exception as e:
            logger.error(f"mcp_server.run() crashed: {e}", exc_info=True)
        finally:
            logger.info("Documentation Agent MCP Server V3 has shut down or exited the main run loop.")
    else:
        logger.info("Starting MCP server without initial documentation sources. Documentation can be added dynamically using 'index_documentation' tool.")
        try:
            mcp_server.run()
            logger.info("mcp_server.run() completed.")
        except KeyboardInterrupt:
            logger.info("MCP Server shutting down due to KeyboardInterrupt.")
        except Exception as e:
            logger.error(f"mcp_server.run() crashed: {e}", exc_info=True)
        finally:
            logger.info("Documentation Agent MCP Server V3 has shut down or exited the main run loop.") 