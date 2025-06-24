#!/usr/bin/env python3
"""
Documentation Retrieval Tool Demo

This script demonstrates how to use the SupabaseDocsParser as a tool
for selective documentation retrieval, similar to how llms.txt works.
"""

from supabase_docs_parser import SupabaseDocsParser, DocSection
from typing import List, Dict, Optional
import json


class DocsRetrievalTool:
    """A tool for selective documentation retrieval"""
    
    def __init__(self, doc_file: str):
        self.parser = SupabaseDocsParser(doc_file)
        self.parser.read_file()
        self.parser.extract_sections()
        print(f"✅ Loaded {len(self.parser.sections)} documentation sections")
    
    def get_auth_docs(self) -> str:
        """Get all authentication-related documentation"""
        auth_sections = self.parser.get_sections_by_category("Authentication")
        mfa_sections = self.parser.get_sections_by_category("Multi-Factor Authentication")
        admin_sections = self.parser.get_sections_by_category("Admin Functions")
        
        all_auth = auth_sections + mfa_sections + admin_sections
        
        result = "# Authentication Documentation\n\n"
        for section in all_auth:
            result += f"## {section.title}\n"
            if section.description:
                result += f"{section.description}\n\n"
            
            if section.examples:
                result += "### Examples:\n"
                for example in section.examples:
                    result += f"- {example}\n"
                result += "\n"
        
        return result
    
    def get_database_operations_docs(self) -> str:
        """Get all database operation documentation"""
        db_sections = self.parser.get_sections_by_category("Database Operations")
        filter_sections = self.parser.get_sections_by_category("Filters")
        modifier_sections = self.parser.get_sections_by_category("Modifiers")
        
        result = "# Database Operations Documentation\n\n"
        
        # CRUD Operations
        result += "## Core Operations\n"
        for section in db_sections:
            result += f"### {section.title}\n"
            if section.description:
                result += f"{section.description}\n\n"
        
        # Filters
        result += "\n## Query Filters\n"
        for section in filter_sections[:5]:  # Show first 5 filters
            result += f"### {section.title}\n"
            if section.description:
                result += f"{section.description}\n\n"
        
        return result
    
    def get_storage_docs(self) -> str:
        """Get all storage-related documentation"""
        storage_sections = self.parser.get_sections_by_category("Storage")
        
        result = "# Storage Documentation\n\n"
        for section in storage_sections:
            result += f"## {section.title}\n"
            if section.description:
                result += f"{section.description}\n\n"
            
            # Include first code example if available
            if section.code_blocks:
                result += "### Example Code:\n"
                result += f"```python\n{section.code_blocks[0]}\n```\n\n"
        
        return result
    
    def get_specific_method_docs(self, method_name: str) -> Optional[str]:
        """Get documentation for a specific method"""
        sections = self.parser.search_sections(method_name, search_in="title")
        
        if not sections:
            return None
        
        section = sections[0]  # Get first match
        
        result = f"# {section.title}\n\n"
        if section.description:
            result += f"{section.description}\n\n"
        
        result += f"**Category:** {section.category}\n"
        result += f"**Line:** {section.line_start}\n\n"
        
        if section.examples:
            result += "## Examples Available:\n"
            for example in section.examples:
                result += f"- {example}\n"
            result += "\n"
        
        if section.code_blocks:
            result += "## Code Examples:\n"
            for i, code in enumerate(section.code_blocks[:2]):  # Show first 2 code blocks
                result += f"### Example {i+1}:\n"
                result += f"```python\n{code}\n```\n\n"
        
        return result
    
    def get_quick_start_guide(self) -> str:
        """Generate a quick start guide with essential sections"""
        essential_methods = [
            "You can initialize a new Supabase client using the `create_client()` method.",
            "Fetch data: select()",
            "Create data: insert()",
            "sign_up()",
            "sign_in_with_password"
        ]
        
        result = "# Supabase Quick Start Guide\n\n"
        
        for method in essential_methods:
            section = self.parser.get_section_by_title(method)
            if section:
                result += f"## {section.title}\n"
                if section.description:
                    result += f"{section.description}\n\n"
                
                # Include first code example
                if section.code_blocks:
                    result += f"```python\n{section.code_blocks[0]}\n```\n\n"
        
        return result
    
    def search_and_extract(self, query: str, max_results: int = 5) -> str:
        """Search and extract relevant documentation"""
        results = self.parser.search_sections(query)[:max_results]
        
        if not results:
            return f"No documentation found for query: '{query}'"
        
        output = f"# Search Results for '{query}'\n\n"
        output += f"Found {len(results)} relevant sections:\n\n"
        
        for i, section in enumerate(results, 1):
            output += f"## {i}. {section.title}\n"
            output += f"**Category:** {section.category} | **Line:** {section.line_start}\n\n"
            
            if section.description:
                output += f"{section.description}\n\n"
            
            if section.examples:
                output += f"**Examples available:** {len(section.examples)}\n\n"
        
        return output
    
    def create_custom_docs(self, categories: List[str], output_file: str = None) -> str:
        """Create custom documentation with selected categories"""
        result = "# Custom Supabase Documentation\n\n"
        
        for category in categories:
            sections = self.parser.get_sections_by_category(category)
            if sections:
                result += f"# {category}\n\n"
                
                for section in sections:
                    result += f"## {section.title}\n"
                    if section.description:
                        result += f"{section.description}\n\n"
                    
                    if section.examples:
                        result += f"**Examples:** {len(section.examples)} available\n"
                    
                    result += f"**Reference:** Line {section.line_start}\n\n"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(result)
        
        return result


def main():
    """Demonstrate the documentation retrieval tool"""
    
    # Initialize the tool
    tool = DocsRetrievalTool("references/supabase_llms_full_like.txt")
    
    print("\n🔍 DEMONSTRATION: Documentation Retrieval Tool")
    print("=" * 60)
    
    # 1. Get authentication docs
    print("\n1️⃣ RETRIEVING AUTHENTICATION DOCUMENTATION")
    print("-" * 40)
    auth_docs = tool.get_auth_docs()
    print(f"Generated {len(auth_docs)} characters of auth documentation")
    print("First 300 characters:")
    print(auth_docs[:300] + "...")
    
    # 2. Get specific method documentation
    print("\n2️⃣ GETTING SPECIFIC METHOD: select()")
    print("-" * 40)
    select_docs = tool.get_specific_method_docs("select()")
    if select_docs:
        print("Documentation found:")
        print(select_docs[:400] + "...")
    
    # 3. Search functionality
    print("\n3️⃣ SEARCHING FOR 'upload'")
    print("-" * 40)
    search_results = tool.search_and_extract("upload", max_results=3)
    print(search_results[:500] + "...")
    
    # 4. Generate quick start guide
    print("\n4️⃣ GENERATING QUICK START GUIDE")
    print("-" * 40)
    quick_start = tool.get_quick_start_guide()
    print(f"Generated {len(quick_start)} characters of quick start guide")
    
    # Save quick start to file
    with open("supabase_quick_start.md", "w") as f:
        f.write(quick_start)
    print("✅ Saved to supabase_quick_start.md")
    
    # 5. Create custom documentation
    print("\n5️⃣ CREATING CUSTOM DOCS (Auth + Storage)")
    print("-" * 40)
    custom_docs = tool.create_custom_docs(
        ["Authentication", "Storage"], 
        "custom_supabase_docs.md"
    )
    print(f"Generated {len(custom_docs)} characters of custom documentation")
    print("✅ Saved to custom_supabase_docs.md")
    
    # 6. Show statistics
    print("\n📊 TOOL STATISTICS")
    print("-" * 40)
    categories = {}
    for section in tool.parser.sections:
        categories[section.category] = categories.get(section.category, 0) + 1
    
    for category, count in sorted(categories.items()):
        print(f"   {category}: {count} sections")
    
    print(f"\n✨ Total extractable content: {len(tool.parser.content)} characters")
    print("✨ Tool ready for selective documentation retrieval!")


if __name__ == "__main__":
    main() 