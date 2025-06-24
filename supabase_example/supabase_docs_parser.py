#!/usr/bin/env python3
"""
Supabase Documentation Parser and Retrieval Tool

This script parses documentation files (like llms.txt format) and provides
tools to extract, index, and selectively retrieve documentation sections.
"""

import re
import json
from typing import List, Dict, Tuple, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class DocSection:
    """Represents a documentation section"""
    title: str
    description: str
    content: str
    line_start: int
    line_end: int
    category: str
    examples: List[str]
    code_blocks: List[str]


class SupabaseDocsParser:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.content = ""
        self.lines = []
        self.sections: List[DocSection] = []
        self.index = {}
        
    def read_file(self) -> bool:
        """Read the documentation file"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
                self.lines = self.content.split('\n')
            return True
        except FileNotFoundError:
            print(f"Error: File {self.file_path} not found")
            return False
    
    def extract_sections(self) -> List[DocSection]:
        """Extract all sections with their complete content"""
        sections = []
        i = 0
        
        while i < len(self.lines):
            line = self.lines[i].strip()
            
            # Look for main section headers (# Python Reference)
            if line == '# Python Reference':
                section = self._parse_section(i)
                if section:
                    sections.append(section)
                    i = section.line_end
                else:
                    i += 1
            else:
                i += 1
        
        self.sections = sections
        return sections
    
    def _parse_section(self, start_line: int) -> Optional[DocSection]:
        """Parse a complete section starting from the header line"""
        if start_line >= len(self.lines):
            return None
        
        # Find the title (next non-empty line after header)
        title_line = start_line + 1
        title = ""
        
        while title_line < len(self.lines) and title_line < start_line + 10:
            candidate = self.lines[title_line].strip()
            if candidate and not candidate.startswith('#') and not candidate.startswith('```'):
                title = candidate
                break
            title_line += 1
        
        if not title:
            return None
        
        # Find the end of this section (next # Python Reference or end of file)
        end_line = start_line + 1
        while end_line < len(self.lines):
            if self.lines[end_line].strip() == '# Python Reference':
                break
            end_line += 1
        
        # Extract the content between title and end
        content_lines = self.lines[title_line + 1:end_line]
        content = '\n'.join(content_lines).strip()
        
        # Extract description (first paragraph after title)
        description = self._extract_description(content_lines)
        
        # Extract examples and code blocks
        examples = self._extract_examples(content_lines)
        code_blocks = self._extract_code_blocks(content_lines)
        
        # Categorize the section
        category = self._categorize_section(title)
        
        return DocSection(
            title=title,
            description=description,
            content=content,
            line_start=start_line + 1,
            line_end=end_line,
            category=category,
            examples=examples,
            code_blocks=code_blocks
        )
    
    def _extract_description(self, content_lines: List[str]) -> str:
        """Extract the description (first paragraph) from content"""
        description_lines = []
        found_content = False
        
        for line in content_lines:
            stripped = line.strip()
            
            # Skip empty lines at the beginning
            if not found_content and not stripped:
                continue
            
            # Start collecting description
            if not found_content and stripped and not stripped.startswith('#'):
                found_content = True
            
            if found_content:
                # Stop at first empty line, header, or examples section
                if not stripped or stripped.startswith('#') or stripped.startswith('## Examples'):
                    break
                description_lines.append(stripped)
        
        return ' '.join(description_lines)
    
    def _extract_examples(self, content_lines: List[str]) -> List[str]:
        """Extract example titles/descriptions"""
        examples = []
        in_examples = False
        
        for line in content_lines:
            stripped = line.strip()
            
            if stripped == '## Examples':
                in_examples = True
                continue
            
            if in_examples:
                if stripped.startswith('### '):
                    examples.append(stripped[4:])  # Remove ### prefix
                elif stripped.startswith('##') and not stripped.startswith('###'):
                    break  # End of examples section
        
        return examples
    
    def _extract_code_blocks(self, content_lines: List[str]) -> List[str]:
        """Extract code blocks from the content"""
        code_blocks = []
        current_block = []
        in_code_block = False
        
        for line in content_lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    if current_block:
                        code_blocks.append('\n'.join(current_block))
                        current_block = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
            elif in_code_block:
                current_block.append(line)
        
        return code_blocks
    
    def _categorize_section(self, title: str) -> str:
        """Categorize a section based on its title"""
        title_lower = title.lower()
        
        # Define category mappings
        categories = {
            "Client Setup": ["create_client", "initialize", "client"],
            "Database Operations": ["select()", "insert()", "update()", "upsert()", "delete()", "rpc()", "fetch data", "create data", "modify data"],
            "Filters": ["eq()", "neq()", "gt()", "gte()", "lt()", "lte()", "like()", "ilike()", 
                       "is_()", "in_()", "contains()", "contained_by()", "range_", "overlaps()", 
                       "text_search()", "match()", "not_()", "or_()", "filter()", "using filters"],
            "Modifiers": ["order()", "limit()", "range()", "single()", "maybe_single()", "csv()", 
                         "using modifiers", "using explain"],
            "Authentication": ["sign_up", "sign_in", "sign_out", "reset_password", "verify_otp", 
                              "get_session", "refresh_session", "get_user", "update_user", 
                              "get_user_identities", "link_identity", "unlink_identity", 
                              "reauthenticate", "resend", "set_session", "exchange_code"],
            "Multi-Factor Authentication": ["mfa."],
            "Admin Functions": ["admin", "get_user_by_id", "list_users", "create_user", 
                               "delete_user", "invite_user", "generate_link", "update_user_by_id"],
            "Edge Functions": ["invoke()", "functions"],
            "Realtime": ["subscribe", "channel", "broadcast", "presence", "realtime", "acreate_client"],
            "Storage": ["bucket", "upload", "download", "storage", "from_.", "signed_url"],
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return "Utilities"
    
    def get_section_by_title(self, title: str) -> Optional[DocSection]:
        """Retrieve a section by its exact title"""
        for section in self.sections:
            if section.title == title:
                return section
        return None
    
    def get_sections_by_category(self, category: str) -> List[DocSection]:
        """Retrieve all sections in a specific category"""
        return [section for section in self.sections if section.category == category]
    
    def search_sections(self, query: str, search_in: str = "all") -> List[DocSection]:
        """Search sections by query in title, description, or content"""
        query_lower = query.lower()
        results = []
        
        for section in self.sections:
            match = False
            
            if search_in in ["all", "title"] and query_lower in section.title.lower():
                match = True
            elif search_in in ["all", "description"] and query_lower in section.description.lower():
                match = True
            elif search_in in ["all", "content"] and query_lower in section.content.lower():
                match = True
            
            if match:
                results.append(section)
        
        return results
    
    def get_section_content(self, title: str, include_examples: bool = True) -> Optional[str]:
        """Get the raw content of a section"""
        section = self.get_section_by_title(title)
        if not section:
            return None
        
        if include_examples:
            return section.content
        else:
            # Return content without examples
            lines = section.content.split('\n')
            content_lines = []
            skip_examples = False
            
            for line in lines:
                if line.strip() == '## Examples':
                    skip_examples = True
                elif line.strip().startswith('## ') and not line.strip().startswith('### '):
                    skip_examples = False
                
                if not skip_examples:
                    content_lines.append(line)
            
            return '\n'.join(content_lines).strip()
    
    def export_index(self, output_file: str = None) -> Dict:
        """Export the complete index as JSON"""
        index_data = {
            "total_sections": len(self.sections),
            "categories": {},
            "sections": []
        }
        
        # Group by categories
        for section in self.sections:
            if section.category not in index_data["categories"]:
                index_data["categories"][section.category] = []
            
            index_data["categories"][section.category].append({
                "title": section.title,
                "line_start": section.line_start,
                "description": section.description
            })
            
            # Add full section data
            index_data["sections"].append(asdict(section))
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(index_data, f, indent=2)
        
        return index_data
    
    def display_index(self, show_descriptions: bool = True):
        """Display a formatted index"""
        categories = {}
        for section in self.sections:
            if section.category not in categories:
                categories[section.category] = []
            categories[section.category].append(section)
        
        print("=" * 70)
        print("SUPABASE DOCUMENTATION INDEX")
        print("=" * 70)
        print(f"Total sections: {len(self.sections)}")
        print()
        
        for category, sections in sorted(categories.items()):
            print(f"📁 {category.upper()}")
            print("-" * 50)
            
            for section in sorted(sections, key=lambda x: x.line_start):
                title_display = f"   • {section.title:<30} (Line {section.line_start})"
                print(title_display)
                
                if show_descriptions and section.description:
                    desc = section.description[:80] + "..." if len(section.description) > 80 else section.description
                    print(f"     {desc}")
                
                if section.examples:
                    print(f"     Examples: {len(section.examples)} available")
                print()
        
        print("=" * 70)
    
    def get_quick_reference(self) -> Dict[str, str]:
        """Get a quick reference of common operations"""
        quick_ref = {}
        
        common_operations = {
            "create_client": "Initialize Supabase client",
            "select()": "Fetch/query data",
            "insert()": "Create new records", 
            "update()": "Modify existing records",
            "delete()": "Remove records",
            "sign_up()": "Register new user",
            "sign_in_with_password": "Authenticate user",
            "from_.upload()": "Upload files",
            "from_.download()": "Download files"
        }
        
        for operation, description in common_operations.items():
            for section in self.sections:
                if operation in section.title:
                    quick_ref[description] = f"{section.title} (Line {section.line_start})"
                    break
        
        return quick_ref


def main():
    """Main function demonstrating the parser capabilities"""
    doc_file = "references/supabase_llms_full_like.txt"
    
    if not Path(doc_file).exists():
        print(f"Error: Documentation file '{doc_file}' not found.")
        return
    
    # Initialize parser
    parser = SupabaseDocsParser(doc_file)
    
    if not parser.read_file():
        return
    
    # Extract sections
    sections = parser.extract_sections()
    print(f"Extracted {len(sections)} sections from documentation")
    print()
    
    # Display full index
    parser.display_index(show_descriptions=True)
    
    # Demonstrate search functionality
    print("\n🔍 SEARCH EXAMPLES")
    print("-" * 50)
    
    # Search for authentication
    auth_sections = parser.search_sections("sign_in")
    print(f"Found {len(auth_sections)} sections related to 'sign_in':")
    for section in auth_sections[:3]:  # Show first 3
        print(f"   • {section.title}")
    
    # Get specific section
    print(f"\n📖 SECTION DETAIL EXAMPLE")
    print("-" * 50)
    select_section = parser.get_section_by_title("Fetch data: select()")
    if select_section:
        print(f"Title: {select_section.title}")
        print(f"Category: {select_section.category}")
        print(f"Description: {select_section.description}")
        print(f"Examples available: {len(select_section.examples)}")
        if select_section.examples:
            print("Example topics:")
            for example in select_section.examples[:3]:
                print(f"   • {example}")
    
    # Export index
    print(f"\n💾 EXPORTING INDEX")
    print("-" * 50)
    index_data = parser.export_index("supabase_index.json")
    print(f"Index exported to supabase_index.json")
    print(f"Categories: {list(index_data['categories'].keys())}")


if __name__ == "__main__":
    main() 