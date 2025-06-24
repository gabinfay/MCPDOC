#!/usr/bin/env python3
"""
Documentation Unflattener

This script processes a single, large, concatenated documentation file (like the
Supabase llms-full.txt) and "unflattens" it into a structured directory of
individual markdown files, organized by category.

This prepares the documentation for a RAG (Retrieval-Augmented Generation)
system that works with a corpus of documents.
"""
import os
import re
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class DocSection:
    """Represents a documentation section parsed from the flat file."""
    title: str
    content: str
    category: str
    line_start: int
    line_end: int  # Line number where the section ends (exclusive)


class FlatDocProcessor:
    """
    Parses a flat documentation file and creates a structured folder of
    markdown files from it.
    """

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.lines: List[str] = []
        self.sections: List[DocSection] = []

    def read_file(self) -> bool:
        """Reads and loads the content of the documentation file."""
        if not self.file_path.exists():
            print(f"Error: Input file not found at '{self.file_path}'")
            return False
        self.lines = self.file_path.read_text(encoding='utf-8').split('\n')
        return True

    def parse_sections(self, primary_marker: str = "# Python Reference"):
        """
        Parses the loaded lines into a list of structured DocSection objects
        based on a recurring header marker.
        """
        i = 0
        while i < len(self.lines):
            line = self.lines[i].strip()
            if line == primary_marker:
                section = self._parse_section(i, primary_marker)
                if section:
                    self.sections.append(section)
                    i = section.line_end
                else:
                    i += 1
            else:
                i += 1

    def _parse_section(self, start_line: int, primary_marker: str) -> Optional[DocSection]:
        """Parses a single section starting from a marker line."""
        title = ""
        title_line_idx = -1
        # Find the title: the first non-empty, non-header line after the marker
        for i in range(start_line + 1, min(start_line + 10, len(self.lines))):
            candidate = self.lines[i].strip()
            if candidate and not candidate.startswith('#'):
                title = candidate
                title_line_idx = i
                break
        
        if not title:
            return None

        # Find the end of the section (the next primary marker or EOF)
        end_line_idx = len(self.lines)
        for i in range(start_line + 1, len(self.lines)):
            if self.lines[i].strip() == primary_marker:
                end_line_idx = i
                break
        
        content = '\n'.join(self.lines[title_line_idx + 1:end_line_idx]).strip()
        category = self._categorize_section(title)
        
        return DocSection(
            title=title,
            content=content,
            category=category,
            line_start=start_line,
            line_end=end_line_idx
        )

    def _categorize_section(self, title: str) -> str:
        """Assigns a category to a section based on keywords in its title."""
        title_lower = title.lower()
        # Order matters: more specific categories should come first.
        categories = {
            "Multi_Factor_Authentication": ["mfa."],
            "Admin_Functions": ["get_user_by_id", "list_users", "create_user", "delete_user", "invite_user", "generate_link", "update_user_by_id"],
            "Authentication": ["sign_up", "sign_in", "sign_out", "reset_password", "verify_otp", "get_session", "refresh_session", "get_user", "update_user", "get_user_identities", "link_identity", "unlink_identity", "reauthenticate", "resend", "set_session", "exchange_code"],
            "Database_Operations": ["select()", "insert()", "update()", "upsert()", "delete()", "rpc()", "fetch data", "create data", "modify data"],
            "Filters": ["eq()", "neq()", "gt()", "gte()", "lt()", "lte()", "like()", "ilike()", "is_()", "in_()", "contains()", "contained_by()", "range_", "overlaps()", "text_search()", "match()", "not_()", "or_()", "filter()", "using filters"],
            "Modifiers": ["order()", "limit()", "range()", "single()", "maybe_single()", "csv()", "using modifiers", "using explain"],
            "Storage": ["bucket", "upload", "download", "storage", "from_.", "signed_url"],
            "Edge_Functions": ["invoke()", "functions"],
            "Realtime": ["subscribe", "channel", "broadcast", "presence", "realtime", "acreate_client"],
            "Client_Setup": ["create_client", "initialize", "client"],
        }
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        return "Utilities"

    def create_docs_folder(self, output_dir: str):
        """Creates a folder structure with markdown files from parsed sections."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        file_count = 0
        category_counts = {}
        
        for section in self.sections:
            category_path = output_path / section.category
            category_path.mkdir(exist_ok=True)
            
            # Sanitize the title to create a valid filename
            safe_filename = re.sub(r'[^\w\s-]', '', section.title)
            safe_filename = re.sub(r'[\s._()]+', '_', safe_filename).strip('_-')
            if not safe_filename:
                safe_filename = f"section_at_line_{section.line_start}"
            safe_filename += ".md"
            
            file_path = category_path / safe_filename
            
            # The content of the new file will be its title as an H1
            # header followed by its original content.
            file_content = f"# {section.title}\n\n{section.content}"
            file_path.write_text(file_content, encoding='utf-8')
            
            file_count += 1
            category_counts[section.category] = category_counts.get(section.category, 0) + 1
            
        print(f"\n✅ Successfully created {file_count} documentation files in '{output_dir}'.")
        print("   Category distribution:")
        for category, count in sorted(category_counts.items()):
            print(f"   - {category}: {count} files")


def main():
    """Main execution block."""
    input_file = "references/supabase.txt"
    output_dir = "supabase_docs_generated"
    
    print(f"▶️ Starting documentation unflattening process...")
    print(f"  Input file: '{input_file}'")
    print(f"  Output directory: '{output_dir}'")
    
    processor = FlatDocProcessor(input_file)
    if not processor.read_file():
        return
        
    print("\nParsing sections from flat file...")
    processor.parse_sections()
    print(f"  Found {len(processor.sections)} distinct sections.")
    
    print("\nCreating structured documentation folder...")
    processor.create_docs_folder(output_dir)
    print("\n⏹️ Process complete.")


if __name__ == "__main__":
    main() 