#!/usr/bin/env python3
"""
Complete Documentation Scraper
===============================

This script does 4 things:
1. Scrapes a documentation website and finds all links
2. Creates llms.txt with organized links (like mem0_llms.txt format)
3. Creates llms-full.txt with concatenated content of all pages
4. Downloads all documentation preserving folder structure

Usage:
    python complete_docs_scraper.py --url https://docs.example.com/ --output docs_folder

Requirements:
    pip install playwright beautifulsoup4 markdownify requests
    playwright install
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
import os
import re
import time
from markdownify import markdownify as md
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import glob

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
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(base_url, href)
        parsed_full_url = urlparse(full_url)
        normalized_url = parsed_full_url._replace(fragment="", query="").geturl()
        if normalized_url.startswith(subdomain_to_keep):
            links.add(normalized_url)
    return links

def scrape_single_page(url, subdomain_to_keep_filter, output_folder, timeout=30000):
    """Scrape a single page with improved error handling and retry logic."""
    start_time = time.time()
    max_retries = 2
    retry_count = 0

    while retry_count <= max_retries:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={'width': 1280, 'height': 720}
                )
                page = context.new_page()
                
                html_content = None
                actual_url_processed = url 
                
                try:
                    response = page.goto(url, timeout=timeout, wait_until='domcontentloaded')
                    if response:
                        actual_url_processed = response.url
                    
                    # Wait for dynamic content
                    page.wait_for_timeout(2000)
                    html_content = page.content()
                    
                except Exception as e:
                    print(f"Attempt {retry_count + 1}: Error loading {url}: {e}")
                    if retry_count < max_retries:
                        retry_count += 1
                        browser.close()
                        time.sleep(1)
                        continue
                    else:
                        browser.close()
                        return None
                
                browser.close()
                break

        except Exception as e:
            print(f"Browser error for {url}: {e}")
            if retry_count < max_retries:
                retry_count += 1
                time.sleep(1)
                continue
            else:
                return None

    if not html_content:
        print(f"Failed to get content from {url} after {max_retries + 1} attempts.")
        return None

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        title_tag = soup.find('title')
        page_title = title_tag.string.strip() if title_tag else urlparse(actual_url_processed).path.split('/')[-1] or "Untitled"
        page_title = page_title.replace('\n', '').replace('\r', '')

        # Skip error pages
        if any(indicator in page_title.lower() for indicator in ['page not found', '404', 'error', 'not found']):
            print(f"Skipping error page: {actual_url_processed} (Title: {page_title})")
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
            print(f"No suitable content element found for {actual_url_processed}")
            return None

        # Remove unwanted elements
        for unwanted in content_element.find_all(['script', 'style', 'nav', 'header', 'footer', '.sidebar', '.navigation']):
            unwanted.decompose()

        markdown_content = md(str(content_element), heading_style="atx", bullets_style="-")
        
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
            print(f"Skipping page with minimal content: {actual_url_processed}")
            return None
        
        # Create folder structure based on URL path
        parsed_actual_url = urlparse(actual_url_processed)
        url_path = parsed_actual_url.path.strip('/')
        
        if url_path:
            path_parts = url_path.split('/')
            folder_path = os.path.join(output_folder, *path_parts[:-1]) if len(path_parts) > 1 else output_folder
            base_filename = sanitize_filename(path_parts[-1]) if path_parts[-1] else "index"
        else:
            folder_path = output_folder
            base_filename = "index"
        
        os.makedirs(folder_path, exist_ok=True)
        saved_filepath = os.path.join(folder_path, f"{base_filename}.md")

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
        print(f"Content processing error for {url}: {e}")
        return None

def generate_llms_txt(scraped_files_meta, output_folder):
    """Generate llms.txt file in mem0 format."""
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
    
    print(f"✅ Generated llms.txt at: {llms_file_path}")
    return llms_file_path

def generate_llms_full_txt(scraped_files_meta, output_folder):
    """Generate llms-full.txt with concatenated content."""
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
    
    print(f"✅ Generated llms-full.txt at: {llms_full_path}")
    return llms_full_path

def main():
    parser = argparse.ArgumentParser(description='Complete Documentation Scraper')
    parser.add_argument('--url', required=True, help='Starting URL to crawl')
    parser.add_argument('--keep', help='Subdomain/path to keep (defaults to same as start URL)')
    parser.add_argument('--output', default='docs', help='Output folder name (default: docs)')
    parser.add_argument('--max-workers', type=int, default=8, help='Max parallel workers (default: 8)')
    parser.add_argument('--max-urls', type=int, default=500, help='Max URLs to process (default: 500)')
    parser.add_argument('--timeout', type=int, default=30000, help='Page timeout in ms (default: 30000)')
    
    args = parser.parse_args()
    
    start_url = args.url.rstrip('/')
    subdomain_to_keep = args.keep or start_url
    output_folder = args.output
    max_workers = args.max_workers
    max_urls = args.max_urls
    timeout = args.timeout
    
    # Ensure subdomain_to_keep ends with /
    parsed_s_to_keep = urlparse(subdomain_to_keep)
    if not subdomain_to_keep.endswith('/') and (not parsed_s_to_keep.path or parsed_s_to_keep.path.endswith('/') or '.' not in parsed_s_to_keep.path.split('/')[-1]):
        subdomain_to_keep += '/'
    
    print("🚀 Complete Documentation Scraper")
    print("=" * 50)
    print(f"📍 Start URL: {start_url}")
    print(f"🎯 Keep URLs matching: {subdomain_to_keep}")
    print(f"📁 Output folder: {output_folder}")
    print(f"👥 Max workers: {max_workers}")
    print(f"🔢 Max URLs: {max_urls}")
    print(f"⏱️  Timeout: {timeout}ms")
    print()
    
    os.makedirs(output_folder, exist_ok=True)
    
    overall_start_time = time.time()
    master_visited_urls = set()       
    master_to_visit_urls_q = {start_url}
    all_scraped_results = {}     
    urls_processed_count = 0
    successful_scrapes = 0
    failed_scrapes = 0
    
    print("🔍 Phase 1: Discovering and scraping pages...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url_map = {}
        
        while (master_to_visit_urls_q or future_to_url_map) and urls_processed_count < max_urls:
            # Submit new tasks
            while master_to_visit_urls_q and len(future_to_url_map) < max_workers and urls_processed_count < max_urls:
                current_url_to_fetch = master_to_visit_urls_q.pop()
                normalized_url = urlparse(current_url_to_fetch)._replace(fragment="", query="").geturl()

                if normalized_url in master_visited_urls:
                    continue 

                master_visited_urls.add(normalized_url) 
                urls_processed_count += 1
                print(f"[{time.time() - overall_start_time:.1f}s] 📤 Submitting ({urls_processed_count}/{max_urls}): {normalized_url}")
                
                future = executor.submit(scrape_single_page, normalized_url, subdomain_to_keep, output_folder, timeout)
                future_to_url_map[future] = normalized_url

            if not future_to_url_map:
                if not master_to_visit_urls_q: 
                    break 
                time.sleep(0.1) 
                continue

            # Process completed tasks
            for future in as_completed(future_to_url_map):
                original_submitted_url = future_to_url_map.pop(future)
                try:
                    result = future.result()

                    if result:
                        successful_scrapes += 1
                        print(f"[{time.time() - overall_start_time:.1f}s] ✅ SUCCESS: {result['actual_url']} -> {os.path.relpath(result['file_path'], output_folder)} ({result['processing_time']:.1f}s)")
                        all_scraped_results[original_submitted_url] = result
                        
                        # Add new discovered links to queue
                        for link in result['links']:
                            norm_link = urlparse(link)._replace(fragment="", query="").geturl()
                            if norm_link.startswith(subdomain_to_keep) and norm_link not in master_visited_urls and norm_link not in master_to_visit_urls_q:
                                master_to_visit_urls_q.add(norm_link)
                    else:
                        failed_scrapes += 1
                        print(f"[{time.time() - overall_start_time:.1f}s] ❌ FAILED: {original_submitted_url}")
                            
                except Exception as exc:
                    failed_scrapes += 1
                    print(f"[{time.time() - overall_start_time:.1f}s] ❌ EXCEPTION for {original_submitted_url}: {exc}")
    
    overall_end_time = time.time()
    
    print()
    print("📊 Scraping Results:")
    print(f"⏱️  Total time: {overall_end_time - overall_start_time:.1f} seconds")
    print(f"🔢 URLs processed: {len(master_visited_urls)}")
    print(f"✅ Successful: {successful_scrapes}")
    print(f"❌ Failed: {failed_scrapes}")
    print(f"📈 Success rate: {successful_scrapes / max(urls_processed_count, 1) * 100:.1f}%")
    print()
    
    if not all_scraped_results:
        print("❌ No files were successfully scraped. Exiting.")
        return
    
    print("🔗 Phase 2: Generating llms.txt...")
    llms_path = generate_llms_txt(all_scraped_results, output_folder)
    
    print("📝 Phase 3: Generating llms-full.txt...")
    llms_full_path = generate_llms_full_txt(all_scraped_results, output_folder)
    
    print()
    print("🎉 Complete! All 4 tasks finished:")
    print(f"📁 1. Downloaded content to: {output_folder}")
    print(f"🔗 2. Links index: {llms_path}")
    print(f"📄 3. Full content: {llms_full_path}")
    print(f"🗂️  4. Folder structure preserved")
    print()
    print(f"📊 Final stats: {successful_scrapes} pages scraped successfully")

if __name__ == "__main__":
    main() 