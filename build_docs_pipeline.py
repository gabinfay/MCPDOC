#!/usr/bin/env python3
"""
End-to-End Documentation Processing Pipeline

This script orchestrates the entire process of converting a flat documentation
file into a structured, summarized, and consolidated corpus ready for a RAG
(Retrieval-Augmented Generation) system.

The pipeline includes:
1. Parsing a flat file into in-memory sections.
2. Analyzing token counts for each category.
3. Consolidating small categories into single files based on a token threshold.
4. Writing the final, optimized file structure to disk.
5. Generating a detailed, AI-summarized master index (`detailed_index.md`).
"""

import os
import re
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import tiktoken
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
INPUT_FILE = "references/supabase.txt"
OUTPUT_DIR = "supabase_docs_final"
TOKEN_THRESHOLD = 10000  # Consolidate categories at or below this token count
PRIMARY_MARKER = "# Python Reference"
OPENAI_MODEL = "gpt-4o-mini" # Model for summarization


@dataclass
class DocSection:
    """Represents a single documentation section parsed from the flat file."""
    title: str
    content: str
    category: str
    line_start: int
    token_count: int

@dataclass
class FinalDoc:
    """Represents a final documentation file to be written to disk."""
    category: str
    filename: str
    content: str
    original_titles: List[str] = field(default_factory=list)
    is_merged: bool = False

class DocsPipeline:
    def __init__(self, input_file, output_dir, threshold, marker):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.threshold = threshold
        self.marker = marker
        self.lines: List[str] = []
        self.sections_by_category: Dict[str, List[DocSection]] = {}
        
        try:
            self.tokenizer = tiktoken.get_encoding("gpt2")
        except Exception:
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def run(self):
        """Executes the entire documentation processing pipeline."""
        print(f"▶️ Starting Documentation Pipeline...")
        print(f"  Input: '{self.input_file}', Output: '{self.output_dir}', Threshold: {self.threshold:,} tokens")

        if not self.input_file.exists():
            print(f"❌ Error: Input file not found at '{self.input_file}'")
            return
            
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ Error: OPENAI_API_KEY environment variable is not set. Summarization will fail.")
            return

        # 1. & 2. Parse and Analyze In-Memory
        self._parse_and_analyze()
        
        # 3. Consolidate In-Memory
        final_docs = self._consolidate_in_memory()
        
        # 4. Write Final Structure to Disk
        self._write_final_docs(final_docs)
        
        # 5. Generate Detailed Index with AI Summaries
        await self._generate_detailed_index()
        
        print("\n⏹️ Pipeline complete.")

    def _parse_and_analyze(self):
        """
        Reads the input file and parses it into categorized sections, calculating
        token counts along the way.
        """
        print("\n[Step 1/5] Parsing and analyzing file in-memory...")
        self.lines = self.input_file.read_text(encoding='utf-8').split('\n')
        
        i = 0
        while i < len(self.lines):
            if self.lines[i].strip() == self.marker:
                section_data = self._parse_single_section_data(i)
                if section_data:
                    title, content, category, start_line, end_line = section_data
                    token_count = len(self.tokenizer.encode(content))
                    
                    section = DocSection(title, content, category, start_line, token_count)
                    
                    if category not in self.sections_by_category:
                        self.sections_by_category[category] = []
                    self.sections_by_category[category].append(section)
                    
                    i = end_line
                else:
                    i += 1
            else:
                i += 1
        print(f"  Parsed {sum(len(s) for s in self.sections_by_category.values())} sections into {len(self.sections_by_category)} categories.")

    def _parse_single_section_data(self, start_line: int) -> Optional[tuple]:
        """Helper to parse one section and return its raw data."""
        title, title_line_idx = "", -1
        for i in range(start_line + 1, min(start_line + 10, len(self.lines))):
            candidate = self.lines[i].strip()
            if candidate and not candidate.startswith('#'):
                title, title_line_idx = candidate, i
                break
        if not title: return None

        end_line_idx = len(self.lines)
        for i in range(start_line + 1, len(self.lines)):
            if self.lines[i].strip() == self.marker:
                end_line_idx = i
                break
        
        content = '\n'.join(self.lines[title_line_idx + 1:end_line_idx]).strip()
        category = self._categorize_section(title)
        return title, content, category, start_line, end_line_idx

    def _categorize_section(self, title: str) -> str:
        """Assigns a category to a section based on keywords in its title."""
        title_lower = title.lower()
        categories = {
            "Multi_Factor_Authentication": ["mfa."], "Admin_Functions": ["get_user_by_id", "list_users", "create_user", "delete_user", "invite_user"],
            "Authentication": ["sign_up", "sign_in", "sign_out", "reset_password", "verify_otp", "get_session", "refresh_session", "get_user"],
            "Database_Operations": ["select()", "insert()", "update()", "upsert()", "delete()", "rpc()"], "Filters": ["eq()", "neq()", "gt()", "gte()", "lt()", "lte()", "like()", "ilike()", "is_()", "in_()", "filter()"],
            "Modifiers": ["order()", "limit()", "range()", "single()", "maybe_single()", "csv()"], "Storage": ["bucket", "upload", "download", "storage", "from_.", "signed_url"],
            "Edge_Functions": ["invoke()", "functions"], "Realtime": ["subscribe", "channel", "broadcast"], "Client_Setup": ["create_client", "initialize", "client"],
        }
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        return "Utilities"

    def _consolidate_in_memory(self) -> List[FinalDoc]:
        """
        Analyzes category token counts and creates a list of FinalDoc objects,
        merging content for categories under the threshold.
        """
        print("\n[Step 2/5] Consolidating categories in-memory...")
        final_docs: List[FinalDoc] = []
        
        for category, sections in self.sections_by_category.items():
            total_tokens = sum(s.token_count for s in sections)
            
            if 0 < total_tokens <= self.threshold:
                # Merge this category
                print(f"  - Merging '{category}' ({total_tokens:,} tokens)")
                merged_content_parts = [f"# Consolidated Documentation: {category.replace('_', ' ')}\n\nThis file merges {len(sections)} sections.\n"]
                original_titles = []
                for section in sections:
                    merged_content_parts.append(f"\n---\n\n## --- {section.title} ---\n\n{section.content}")
                    original_titles.append(section.title)
                
                final_docs.append(FinalDoc(
                    category=category,
                    filename=f"_merged_{category}.md",
                    content="".join(merged_content_parts),
                    original_titles=original_titles,
                    is_merged=True
                ))
            else:
                # Keep files separate for this category
                print(f"  - Skipping merge for '{category}' ({total_tokens:,} tokens)")
                for section in sections:
                    safe_filename = re.sub(r'[^\w\s-]', '', section.title)
                    safe_filename = re.sub(r'[\s._()]+', '_', safe_filename).strip('_-')
                    final_docs.append(FinalDoc(
                        category=category,
                        filename=f"{safe_filename}.md",
                        content=f"# {section.title}\n\n{section.content}",
                        original_titles=[section.title]
                    ))

        return final_docs

    def _write_final_docs(self, final_docs: List[FinalDoc]):
        """Writes the final documentation structure to the output directory."""
        print(f"\n[Step 3/5] Writing final documentation to '{self.output_dir}'...")
        if self.output_dir.exists():
            import shutil
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir()
        
        for doc in final_docs:
            category_path = self.output_dir / doc.category
            category_path.mkdir(exist_ok=True)
            file_path = category_path / doc.filename
            file_path.write_text(doc.content, encoding='utf-8')
            
            if doc.is_merged:
                index_path = category_path / f"{file_path.stem}_index.txt"
                index_content = f"The file '{doc.filename}' contains the following merged sections:\n\n"
                index_content += "\n".join(sorted(doc.original_titles))
                index_path.write_text(index_content, encoding='utf-8')
        print(f"  Wrote {len(final_docs)} files to disk.")

    async def _generate_detailed_index(self):
        """
        Generates the detailed_index.md file by summarizing each final doc
        file using an AI model.
        """
        print(f"\n[Step 4/5] Generating AI summaries for detailed_index.md...")
        
        # Prepare summarization tasks
        summarization_tasks = []
        final_doc_paths = sorted(list(self.output_dir.glob("**/*.md")))

        for doc_path in final_doc_paths:
            content = doc_path.read_text(encoding='utf-8')
            task = self._get_ai_summary(doc_path.relative_to(self.output_dir), content)
            summarization_tasks.append(task)
            
        # Execute tasks in parallel
        print(f"  Sending {len(summarization_tasks)} documents to '{OPENAI_MODEL}' for summarization...")
        summaries = await asyncio.gather(*summarization_tasks)
        
        # Build the detailed index
        print("\n[Step 5/5] Assembling final detailed_index.md...")
        detailed_index_content = ["# Detailed Documentation Index\n\n"]
        
        for i, doc_path in enumerate(final_doc_paths):
            summary = summaries[i]
            relative_path = doc_path.relative_to(self.output_dir)
            
            detailed_index_content.append(f"## File: `{relative_path}`\n\n")
            detailed_index_content.append("### AI-Generated Summary\n")
            detailed_index_content.append(f"{summary}\n\n")
            
            # If it's a merged file, include the index of its contents
            index_txt_path = doc_path.with_name(f"{doc_path.stem}_index.txt")
            if index_txt_path.exists():
                detailed_index_content.append("### Contained Sections\n")
                detailed_index_content.append("```\n")
                detailed_index_content.append(index_txt_path.read_text(encoding='utf-8'))
                detailed_index_content.append("```\n\n")

            detailed_index_content.append("---\n")
            
        # Write the final index file
        index_file = self.output_dir / "detailed_index.md"
        index_file.write_text("".join(detailed_index_content), encoding='utf-8')
        print(f"  ✅ Successfully created '{index_file}'")

    async def _get_ai_summary(self, doc_path: Path, content: str) -> str:
        """Sends content to OpenAI API for summarization."""
        system_prompt = "You are an expert technical writer. Analyze the following document content and provide a concise (2-3 sentences) overview of its main purpose and key information. Focus on the core functionality described."
        user_prompt = f"""Document Path: '{doc_path}'

Content to analyze:
---
{content[:15000]}
---
"""
        try:
            completion = await self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"  ⚠️  Warning: AI summary failed for {doc_path}. Error: {e}")
            return f"Error: AI summary could not be generated for this file."


if __name__ == "__main__":
    pipeline = DocsPipeline(
        input_file=INPUT_FILE,
        output_dir=OUTPUT_DIR,
        threshold=TOKEN_THRESHOLD,
        marker=PRIMARY_MARKER
    )
    asyncio.run(pipeline.run()) 