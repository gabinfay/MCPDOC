#!/usr/bin/env python3
"""
Indexed Document Tool - Test and Development Script

This script creates and tests the indexed document functionality that will be
integrated into the MCP server. It includes:
1. AI-powered indexing of long markdown documents
2. Selective retrieval based on user queries
3. System prompt generation for the doc agent
"""

import os
import json
import openai
from typing import List, Dict, Optional, Any
from pathlib import Path
from dotenv import load_dotenv
import re

load_dotenv()

class IndexedDocumentTool:
    """Tool for indexing and selectively retrieving from long markdown documents"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required for AI-powered indexing")
        
        self.client = openai.OpenAI(api_key=self.openai_api_key)
        self.indexed_docs = {}  # url -> {index, content, metadata}
        
    def parse_markdown_sections(self, content: str) -> List[Dict[str, Any]]:
        """Parse markdown content into sections based on headers"""
        lines = content.split('\n')
        sections = []
        current_section = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check for headers (# ## ###)
            if line.startswith('#'):
                # Save previous section if exists
                if current_section:
                    current_section['line_end'] = i - 1
                    current_section['content'] = '\n'.join(lines[current_section['line_start']:current_section['line_end'] + 1])
                    sections.append(current_section)
                
                # Start new section
                header_level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('# ').strip()
                
                current_section = {
                    'title': title,
                    'header_level': header_level,
                    'line_start': i,
                    'line_end': None,
                    'content': '',
                    'subsections': []
                }
            
            # Check for "Python Reference" pattern (special case for this format)
            elif line == "# Python Reference" or (line and not line.startswith('#') and current_section is None):
                # This might be a section title following "# Python Reference"
                if current_section:
                    current_section['line_end'] = i - 1
                    current_section['content'] = '\n'.join(lines[current_section['line_start']:current_section['line_end'] + 1])
                    sections.append(current_section)
                
                # Look ahead for the actual section title
                title = line if line != "# Python Reference" else "Overview"
                if line == "# Python Reference" and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not next_line.startswith('#'):
                        title = next_line
                
                current_section = {
                    'title': title,
                    'header_level': 1,
                    'line_start': i,
                    'line_end': None,
                    'content': '',
                    'subsections': []
                }
        
        # Add final section
        if current_section:
            current_section['line_end'] = len(lines) - 1
            current_section['content'] = '\n'.join(lines[current_section['line_start']:current_section['line_end'] + 1])
            sections.append(current_section)
        
        return sections

    def generate_ai_description(self, section_content: str, section_title: str) -> str:
        """Generate AI description for a single section (fallback method)"""
        try:
            system_prompt = """You are an expert technical documentation analyst. 
Your task is to analyze code documentation sections and provide concise, accurate descriptions.
Focus on what the section teaches, what functionality it covers, and key concepts.
Keep descriptions to 1-2 sentences maximum."""
            
            user_prompt = f"""Analyze this documentation section titled "{section_title}":

{section_content[:1000]}...

Provide a concise description (1-2 sentences) of what this section covers and its main purpose."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating AI description: {e}")
            return f"Documentation section about {section_title}"

    def categorize_section(self, title: str, content: str) -> str:
        """Categorize a section based on its title and content"""
        title_lower = title.lower()
        content_lower = content.lower()
        
        # Authentication
        if any(term in title_lower for term in ['auth', 'sign_in', 'sign_up', 'login', 'logout', 'user']):
            if 'mfa' in title_lower or 'multi-factor' in title_lower:
                return "Multi-Factor Authentication"
            elif 'admin' in title_lower:
                return "Admin Functions"
            else:
                return "Authentication"
        
        # Database operations
        elif any(term in title_lower for term in ['select', 'insert', 'update', 'delete', 'upsert', 'rpc']):
            return "Database Operations"
        
        # Filters
        elif any(term in title_lower for term in ['eq()', 'neq()', 'gt()', 'gte()', 'lt()', 'lte()', 'like', 'filter']):
            return "Filters"
        
        # Modifiers
        elif any(term in title_lower for term in ['order', 'limit', 'range', 'single', 'csv']):
            return "Modifiers"
        
        # Storage
        elif any(term in title_lower for term in ['storage', 'upload', 'download', 'bucket', 'file']):
            return "Storage"
        
        # Realtime
        elif any(term in title_lower for term in ['realtime', 'subscribe', 'channel', 'broadcast']):
            return "Realtime"
        
        # Edge Functions
        elif any(term in title_lower for term in ['invoke', 'function', 'edge']):
            return "Edge Functions"
        
        # Client setup
        elif any(term in title_lower for term in ['client', 'create_client', 'initialize']):
            return "Client Setup"
        
        else:
            return "General"

    def estimate_api_calls(self, file_path: str, batch_size: int = 10) -> Dict[str, Any]:
        """Estimate API calls needed without making them"""
        print(f"📊 Estimating API calls for: {file_path}")
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse sections
        sections = self.parse_markdown_sections(content)
        
        # Calculate batching
        batched_api_calls = (len(sections) + batch_size - 1) // batch_size
        
        estimate = {
            "total_sections": len(sections),
            "single_api_calls_needed": len(sections),  # One call per section (old way)
            "batched_api_calls_needed": batched_api_calls,  # Batched approach
            "batch_size": batch_size,
            "api_call_reduction": len(sections) - batched_api_calls,
            "cost_reduction_percent": round((1 - batched_api_calls / len(sections)) * 100, 1),
            "estimated_cost_single_usd": len(sections) * 0.0001,  # Old approach
            "estimated_cost_batched_usd": batched_api_calls * 0.0005,  # Batched (more tokens per call)
            "sections_preview": []
        }
        
        # Show preview of first 10 sections
        for i, section in enumerate(sections[:10]):
            estimate["sections_preview"].append({
                "title": section['title'][:100],
                "content_length": len(section['content']),
                "line_range": f"{section['line_start']}-{section['line_end']}"
            })
        
        return estimate

    def index_document(self, file_path: str, doc_url: str = None, skip_ai: bool = False) -> Dict[str, Any]:
        """Index a markdown document with AI-generated descriptions"""
        print(f"📄 Indexing document: {file_path}")
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse sections
        sections = self.parse_markdown_sections(content)
        print(f"📝 Found {len(sections)} sections")
        
        # Generate detailed index
        detailed_index = {
            "document_info": {
                "file_path": file_path,
                "doc_url": doc_url or file_path,
                "total_sections": len(sections),
                "indexed_at": "2024-01-01"  # Would be actual timestamp
            },
            "categories": {},
            "sections": []
        }
        
        # Process each section
        for i, section in enumerate(sections):
            if i % 50 == 0:  # Progress update every 50 sections
                print(f"🔍 Processing section {i+1}/{len(sections)}: {section['title'][:50]}...")
            
            # Generate AI description (or skip if requested)
            if skip_ai:
                ai_description = f"Auto-categorized section about {section['title']}"
            else:
                ai_description = self.generate_ai_description(section['content'], section['title'])
            
            # Categorize
            category = self.categorize_section(section['title'], section['content'])
            
            # Extract code blocks
            code_blocks = re.findall(r'```python\n(.*?)\n```', section['content'], re.DOTALL)
            
            section_data = {
                "id": f"section_{i}",
                "title": section['title'],
                "category": category,
                "ai_description": ai_description,
                "line_start": section['line_start'],
                "line_end": section['line_end'],
                "header_level": section['header_level'],
                "has_code_examples": len(code_blocks) > 0,
                "code_examples_count": len(code_blocks),
                "content_preview": section['content'][:200] + "..." if len(section['content']) > 200 else section['content']
            }
            
            detailed_index["sections"].append(section_data)
            
            # Add to categories
            if category not in detailed_index["categories"]:
                detailed_index["categories"][category] = []
            detailed_index["categories"][category].append(section_data)
        
        # Store in memory
        self.indexed_docs[doc_url or file_path] = {
            "index": detailed_index,
            "content": content,
            "sections": sections
        }
        
        print(f"✅ Indexing complete! Generated index with {len(detailed_index['sections'])} sections")
        return detailed_index

    def query_relevant_sections(self, query: str, doc_url: str, max_sections: int = 5) -> List[Dict[str, Any]]:
        """Find relevant sections based on a user query"""
        if doc_url not in self.indexed_docs:
            return []
        
        doc_data = self.indexed_docs[doc_url]
        sections = doc_data["index"]["sections"]
        
        query_lower = query.lower()
        scored_sections = []
        
        for section in sections:
            score = 0
            
            # Title matching (highest weight)
            if query_lower in section["title"].lower():
                score += 10
            
            # Category matching
            if query_lower in section["category"].lower():
                score += 5
            
            # AI description matching
            if query_lower in section["ai_description"].lower():
                score += 7
            
            # Content preview matching
            if query_lower in section["content_preview"].lower():
                score += 3
            
            # Specific method matching
            for word in query_lower.split():
                if word in section["title"].lower():
                    score += 2
                if word in section["ai_description"].lower():
                    score += 1
            
            if score > 0:
                section_with_score = section.copy()
                section_with_score["relevance_score"] = score
                scored_sections.append(section_with_score)
        
        # Sort by relevance score and return top results
        scored_sections.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_sections[:max_sections]

    def get_section_content(self, doc_url: str, section_id: str) -> Optional[str]:
        """Get the full content of a specific section"""
        if doc_url not in self.indexed_docs:
            return None
        
        doc_data = self.indexed_docs[doc_url]
        sections = doc_data["sections"]
        
        # Find section by ID
        section_index = int(section_id.split('_')[1]) if section_id.startswith('section_') else -1
        if 0 <= section_index < len(sections):
            return sections[section_index]["content"]
        
        return None

    def generate_system_prompt_context(self, query: str, doc_url: str) -> str:
        """Generate system prompt context with relevant sections"""
        relevant_sections = self.query_relevant_sections(query, doc_url)
        
        if not relevant_sections:
            return "No relevant documentation found for this query."
        
        context = f"# Relevant Documentation for Query: '{query}'\n\n"
        
        for i, section in enumerate(relevant_sections, 1):
            context += f"## {i}. {section['title']}\n"
            context += f"**Category:** {section['category']}\n"
            context += f"**Description:** {section['ai_description']}\n"
            
            # Get full content
            full_content = self.get_section_content(doc_url, section['id'])
            if full_content:
                context += f"**Content:**\n{full_content}\n\n"
            else:
                context += f"**Content Preview:** {section['content_preview']}\n\n"
            
            context += "---\n\n"
        
        return context


def test_indexed_document_tool():
    """Test the indexed document functionality"""
    print("🧪 Testing Indexed Document Tool")
    print("=" * 50)
    
    # Initialize tool
    try:
        tool = IndexedDocumentTool()
        print("✅ Tool initialized successfully")
    except ValueError as e:
        print(f"❌ Failed to initialize tool: {e}")
        return
    
    # Test file path
    test_file = "supabase_example/supabase_llms_full_like.txt"
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    # First, estimate API calls
    print(f"\n📊 Estimating API calls needed...")
    doc_url = "https://docs.supabase.com/llms.txt"
    
    try:
        estimate = tool.estimate_api_calls(test_file)
        print(f"📈 API Call Estimate:")
        print(f"   - Total sections: {estimate['total_sections']}")
        print(f"   - API calls needed: {estimate['api_calls_needed']}")
        print(f"   - Estimated cost: ${estimate['estimated_cost_usd']:.4f}")
        print(f"\n📋 First 10 sections preview:")
        for i, section in enumerate(estimate['sections_preview'], 1):
            print(f"   {i}. {section['title']} (lines {section['line_range']}, {section['content_length']} chars)")
        
        # Ask user before proceeding
        if estimate['api_calls_needed'] > 50:
            print(f"\n⚠️  Warning: This will make {estimate['api_calls_needed']} API calls")
            print("This might be expensive. Consider batching or using skip_ai=True for testing.")
        
        # Ask user if they want to proceed with AI indexing
        proceed_with_ai = False
        if estimate['api_calls_needed'] <= 50:
            proceed_with_ai = True
            print(f"\n🤖 Proceeding with AI indexing (cost is reasonable)")
        else:
            print(f"\n📄 Testing document indexing (without AI descriptions first)...")
        
        index = tool.index_document(test_file, doc_url, skip_ai=not proceed_with_ai)
        print(f"✅ Indexing successful!")
        print(f"   - Total sections: {index['document_info']['total_sections']}")
        print(f"   - Categories: {list(index['categories'].keys())}")
        
        # Show sample AI descriptions if they were generated
        if proceed_with_ai and len(index['sections']) > 0:
            print(f"\n📋 Sample AI descriptions:")
            for i, section in enumerate(index['sections'][:3]):
                print(f"   {i+1}. {section['title']}")
                print(f"      → {section['ai_description']}")
        
    except Exception as e:
        print(f"❌ Estimation/Indexing failed: {e}")
        return
    
    # Test queries
    test_queries = [
        "authentication",
        "select data",
        "upload file",
        "create user",
        "filters"
    ]
    
    print(f"\n🔍 Testing queries...")
    for query in test_queries:
        print(f"\n Query: '{query}'")
        relevant_sections = tool.query_relevant_sections(query, doc_url, max_sections=3)
        print(f"   Found {len(relevant_sections)} relevant sections:")
        
        for section in relevant_sections:
            print(f"   - {section['title']} (score: {section['relevance_score']})")
    
    # Test system prompt generation
    print(f"\n📝 Testing system prompt generation...")
    test_query = "How do I authenticate users?"
    context = tool.generate_system_prompt_context(test_query, doc_url)
    print(f"Generated context length: {len(context)} characters")
    print(f"First 500 characters:\n{context[:500]}...")
    
    print(f"\n✅ All tests completed successfully!")
    return tool


if __name__ == "__main__":
    tool = test_indexed_document_tool()