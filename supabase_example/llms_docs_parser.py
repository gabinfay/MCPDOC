#!/usr/bin/env python3
"""
General-purpose Documentation Parser for llms.txt-style files

This is a generic tool that can parse documentation files with section headers
and provide selective retrieval capabilities. It's designed to work with 
llms.txt format and similar documentation structures.
"""

import re
import json
import argparse
from typing import List, Dict, Tuple, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class DocumentSection:
    """Represents a documentation section"""
    title: str
    description: str
    content: str
    line_start: int
    line_end: int
    category: str
    metadata: Dict[str, any]


class LLMSDocsParser:
    """A general-purpose parser for llms.txt-style documentation"""
    
    def __init__(self, file_path: str, section_markers: List[str] = None):
        self.file_path = Path(file_path)
        self.content = ""
        self.lines = []
        self.sections: List[DocumentSection] = []
        
        # Default section markers (can be customized)
        self.section_markers = section_markers or [
            "# Python Reference",
            "## ",
            "# ",
            "###"
        ]
        
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
    
    def extract_sections(self, primary_marker: str = "# Python Reference") -> List[DocumentSection]:
        """Extract all sections based on the primary marker"""
        sections = []
        i = 0
        
        while i < len(self.lines):
            line = self.lines[i].strip()
            
            # Look for primary section markers
            if line == primary_marker:
                section = self._parse_section(i, primary_marker)
                if section:
                    sections.append(section)
                    i = section.line_end
                else:
                    i += 1
            else:
                i += 1
        
        self.sections = sections
        return sections
    
    def _parse_section(self, start_line: int, marker: str) -> Optional[DocumentSection]:
        """Parse a complete section starting from the marker line"""
        if start_line >= len(self.lines):
            return None
        
        # Find the title (next non-empty, non-marker line)
        title_line = start_line + 1
        title = ""
        
        while title_line < len(self.lines) and title_line < start_line + 10:
            candidate = self.lines[title_line].strip()
            if candidate and not self._is_section_marker(candidate):
                title = candidate
                break
            title_line += 1
        
        if not title:
            return None
        
        # Find the end of this section
        end_line = self._find_section_end(start_line + 1, marker)
        
        # Extract content
        content_lines = self.lines[title_line + 1:end_line]
        content = '\n'.join(content_lines).strip()
        
        # Extract description and metadata
        description = self._extract_description(content_lines)
        metadata = self._extract_metadata(content_lines)
        category = self._auto_categorize(title, content)
        
        return DocumentSection(
            title=title,
            description=description,
            content=content,
            line_start=start_line + 1,
            line_end=end_line,
            category=category,
            metadata=metadata
        )
    
    def _is_section_marker(self, line: str) -> bool:
        """Check if a line is a section marker"""
        for marker in self.section_markers:
            if line.startswith(marker):
                return True
        return False
    
    def _find_section_end(self, start: int, primary_marker: str) -> int:
        """Find where the current section ends"""
        i = start
        while i < len(self.lines):
            if self.lines[i].strip() == primary_marker:
                return i
            i += 1
        return len(self.lines)
    
    def _extract_description(self, content_lines: List[str]) -> str:
        """Extract description from the first paragraph"""
        description_lines = []
        found_content = False
        
        for line in content_lines:
            stripped = line.strip()
            
            if not found_content and not stripped:
                continue
            
            if not found_content and stripped and not stripped.startswith('#'):
                found_content = True
            
            if found_content:
                if not stripped or stripped.startswith('#') or stripped.startswith('## Examples'):
                    break
                description_lines.append(stripped)
        
        return ' '.join(description_lines)
    
    def _extract_metadata(self, content_lines: List[str]) -> Dict[str, any]:
        """Extract metadata like examples, code blocks, etc."""
        metadata = {
            "examples": [],
            "code_blocks": [],
            "has_examples": False,
            "line_count": len(content_lines)
        }
        
        # Extract examples
        in_examples = False
        for line in content_lines:
            stripped = line.strip()
            if stripped == '## Examples':
                in_examples = True
                metadata["has_examples"] = True
                continue
            
            if in_examples:
                if stripped.startswith('### '):
                    metadata["examples"].append(stripped[4:])
                elif stripped.startswith('##') and not stripped.startswith('###'):
                    break
        
        # Extract code blocks
        current_block = []
        in_code_block = False
        
        for line in content_lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    if current_block:
                        metadata["code_blocks"].append('\n'.join(current_block))
                        current_block = []
                    in_code_block = False
                else:
                    in_code_block = True
            elif in_code_block:
                current_block.append(line)
        
        return metadata
    
    def _auto_categorize(self, title: str, content: str) -> str:
        """Automatically categorize sections based on content"""
        title_lower = title.lower()
        content_lower = content.lower()
        
        # Define categorization rules
        if any(word in title_lower for word in ['auth', 'sign', 'login', 'user', 'session']):
            return "Authentication"
        elif any(word in title_lower for word in ['select', 'insert', 'update', 'delete', 'query', 'database']):
            return "Database"
        elif any(word in title_lower for word in ['storage', 'upload', 'download', 'file', 'bucket']):
            return "Storage"
        elif any(word in title_lower for word in ['function', 'invoke', 'edge']):
            return "Functions"
        elif any(word in title_lower for word in ['realtime', 'subscribe', 'channel', 'broadcast']):
            return "Realtime"
        elif any(word in title_lower for word in ['filter', 'where', 'eq', 'gt', 'lt']):
            return "Filters"
        elif any(word in title_lower for word in ['order', 'limit', 'range', 'single']):
            return "Modifiers"
        elif any(word in title_lower for word in ['client', 'initialize', 'setup', 'config']):
            return "Configuration"
        else:
            return "General"
    
    def get_section_by_title(self, title: str) -> Optional[DocumentSection]:
        """Get a section by its exact title"""
        for section in self.sections:
            if section.title == title:
                return section
        return None
    
    def get_sections_by_category(self, category: str) -> List[DocumentSection]:
        """Get all sections in a category"""
        return [section for section in self.sections if section.category == category]
    
    def search_sections(self, query: str, search_in: str = "all") -> List[DocumentSection]:
        """Search sections by query"""
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
    
    def get_categories(self) -> Dict[str, int]:
        """Get all categories with section counts"""
        categories = {}
        for section in self.sections:
            categories[section.category] = categories.get(section.category, 0) + 1
        return categories
    
    def export_json(self, output_file: str = None) -> Dict:
        """Export all data as JSON"""
        data = {
            "file_path": str(self.file_path),
            "total_sections": len(self.sections),
            "categories": self.get_categories(),
            "sections": [asdict(section) for section in self.sections]
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        return data
    
    def generate_markdown_index(self, include_descriptions: bool = True) -> str:
        """Generate a markdown index of all sections"""
        categories = {}
        for section in self.sections:
            if section.category not in categories:
                categories[section.category] = []
            categories[section.category].append(section)
        
        result = f"# Documentation Index\n\n"
        result += f"**Source:** {self.file_path}\n"
        result += f"**Total Sections:** {len(self.sections)}\n\n"
        
        for category, sections in sorted(categories.items()):
            result += f"## {category}\n\n"
            
            for section in sorted(sections, key=lambda x: x.line_start):
                result += f"### {section.title}\n"
                result += f"**Line:** {section.line_start}\n"
                
                if include_descriptions and section.description:
                    result += f"**Description:** {section.description[:100]}{'...' if len(section.description) > 100 else ''}\n"
                
                if section.metadata.get("examples"):
                    result += f"**Examples:** {len(section.metadata['examples'])}\n"
                
                result += "\n"
        
        return result
    
    def extract_content(self, titles: List[str] = None, categories: List[str] = None, 
                       query: str = None) -> str:
        """Extract content based on filters"""
        sections_to_include = []
        
        if titles:
            for title in titles:
                section = self.get_section_by_title(title)
                if section:
                    sections_to_include.append(section)
        
        if categories:
            for category in categories:
                sections_to_include.extend(self.get_sections_by_category(category))
        
        if query:
            sections_to_include.extend(self.search_sections(query))
        
        # Remove duplicates
        unique_sections = []
        seen_titles = set()
        for section in sections_to_include:
            if section.title not in seen_titles:
                unique_sections.append(section)
                seen_titles.add(section.title)
        
        # Generate content
        result = "# Extracted Documentation\n\n"
        
        for section in sorted(unique_sections, key=lambda x: x.line_start):
            result += f"## {section.title}\n\n"
            if section.description:
                result += f"{section.description}\n\n"
            
            if section.metadata.get("code_blocks"):
                result += "### Example:\n"
                result += f"```\n{section.metadata['code_blocks'][0]}\n```\n\n"
        
        return result


def main():
    """Command-line interface for the parser"""
    parser = argparse.ArgumentParser(description="Parse llms.txt-style documentation")
    parser.add_argument("file", help="Documentation file to parse")
    parser.add_argument("--marker", default="# Python Reference", 
                       help="Primary section marker")
    parser.add_argument("--export-json", help="Export to JSON file")
    parser.add_argument("--export-markdown", help="Export index to markdown file")
    parser.add_argument("--search", help="Search for sections containing this term")
    parser.add_argument("--category", help="Show sections in this category")
    parser.add_argument("--extract", nargs="+", help="Extract specific section titles")
    
    args = parser.parse_args()
    
    # Initialize parser
    doc_parser = LLMSDocsParser(args.file)
    
    if not doc_parser.read_file():
        return
    
    # Extract sections
    sections = doc_parser.extract_sections(args.marker)
    print(f"✅ Parsed {len(sections)} sections from {args.file}")
    
    # Handle commands
    if args.export_json:
        doc_parser.export_json(args.export_json)
        print(f"✅ Exported JSON to {args.export_json}")
    
    if args.export_markdown:
        index_md = doc_parser.generate_markdown_index()
        with open(args.export_markdown, 'w') as f:
            f.write(index_md)
        print(f"✅ Exported markdown index to {args.export_markdown}")
    
    if args.search:
        results = doc_parser.search_sections(args.search)
        print(f"\n🔍 Search results for '{args.search}':")
        for section in results:
            print(f"   • {section.title} (Line {section.line_start})")
    
    if args.category:
        sections = doc_parser.get_sections_by_category(args.category)
        print(f"\n📁 Sections in category '{args.category}':")
        for section in sections:
            print(f"   • {section.title} (Line {section.line_start})")
    
    if args.extract:
        content = doc_parser.extract_content(titles=args.extract)
        print(f"\n📄 Extracted content:\n")
        print(content[:500] + "..." if len(content) > 500 else content)
    
    # Show summary
    categories = doc_parser.get_categories()
    print(f"\n📊 Categories found:")
    for category, count in sorted(categories.items()):
        print(f"   {category}: {count} sections")


if __name__ == "__main__":
    main() 