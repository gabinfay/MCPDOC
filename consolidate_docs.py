#!/usr/bin/env python3
"""
Documentation Consolidator

This script analyzes a directory of generated documentation files and
consolidates folders that are below a certain token threshold into single,
merged markdown files. This optimizes the structure for RAG systems by
reducing the number of small files.
"""
import os
import shutil
from pathlib import Path
import tiktoken
from typing import Dict, Any, List


class DocsAnalyzer:
    """Analyzes the structure of a documentation folder."""

    def __init__(self, docs_dir: str):
        self.docs_dir = Path(docs_dir)
        if not self.docs_dir.is_dir():
            raise FileNotFoundError(f"Documentation directory not found: '{docs_dir}'")
        
        try:
            self.tokenizer = tiktoken.get_encoding("gpt2")
        except Exception:
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")

    def analyze_structure(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyzes each category subdirectory for file count, line count, and token count.
        """
        analysis_results = {}
        for category_path in self.docs_dir.iterdir():
            if not category_path.is_dir():
                continue
            
            category_name = category_path.name
            category_stats = {"file_count": 0, "total_tokens": 0, "files": []}

            for file_path in sorted(category_path.glob("*.md")):
                content = file_path.read_text(encoding='utf-8')
                tokens = self.tokenizer.encode(content)
                category_stats["file_count"] += 1
                category_stats["total_tokens"] += len(tokens)
                category_stats["files"].append(file_path)
            
            if category_stats["file_count"] > 0:
                analysis_results[category_name] = category_stats
        
        return analysis_results


class DocsConsolidator:
    """Consolidates documentation folders based on a token threshold."""

    def __init__(self, docs_dir: str, threshold: int):
        self.docs_dir = Path(docs_dir)
        self.threshold = threshold
        self.analyzer = DocsAnalyzer(str(docs_dir))

    def consolidate(self):
        """
        Runs the consolidation process: analyzes, identifies candidates,
        and merges them.
        """
        print(f"▶️ Starting consolidation process for '{self.docs_dir}'...")
        print(f"   Threshold set to {self.threshold:,} tokens.")
        
        try:
            analysis_results = self.analyzer.analyze_structure()
        except FileNotFoundError as e:
            print(f"\nError: {e}")
            return

        merged_count = 0
        skipped_count = 0
        
        for category_name, stats in analysis_results.items():
            if 0 < stats['total_tokens'] <= self.threshold:
                print(f"\nMerging category '{category_name}' ({stats['total_tokens']:,} tokens <= {self.threshold:,})")
                self._merge_category(category_name, stats['files'])
                merged_count += 1
            else:
                print(f"\nSkipping category '{category_name}' ({stats['total_tokens']:,} tokens > {self.threshold:,})")
                skipped_count += 1
        
        print("\n" + "="*50)
        print("Consolidation Summary:")
        print(f"  - Categories Merged: {merged_count}")
        print(f"  - Categories Skipped: {skipped_count}")
        print("="*50)


    def _merge_category(self, category_name: str, files_to_merge: List[Path]):
        """
        Merges all markdown files in a category into a single file and
        deletes the originals.
        """
        category_path = self.docs_dir / category_name
        merged_content = []
        original_filenames = []
        
        # Header for the merged file
        merged_content.append(f"# Consolidated Documentation: {category_name.replace('_', ' ')}\n\n")
        merged_content.append(f"This file is a consolidation of {len(files_to_merge)} smaller documents from the '{category_name}' category.\n\n")

        for file_path in files_to_merge:
            original_filenames.append(file_path.name)
            content = file_path.read_text(encoding='utf-8')
            
            # Add a separator and header for each merged file's content
            merged_content.append(f"\n\n---\n\n## --- Merged from: {file_path.name} ---\n\n")
            merged_content.append(content)
        
        # 1. Create the new merged file
        merged_file_path = category_path / f"_merged_{category_name}.md"
        merged_file_path.write_text("".join(merged_content).strip(), encoding='utf-8')
        print(f"  - Created merged file: {merged_file_path.name}")
        
        # 2. Create the index file
        index_file_path = category_path / f"_merged_{category_name}_index.txt"
        index_content = f"The following {len(original_filenames)} files were merged into _merged_{category_name}.md:\n\n"
        index_content += "\n".join(sorted(original_filenames))
        index_file_path.write_text(index_content, encoding='utf-8')
        print(f"  - Created index file: {index_file_path.name}")
        
        # 3. Delete the original files
        for file_path in files_to_merge:
            file_path.unlink()
        print(f"  - Removed {len(original_filenames)} original files.")


def main():
    """Main execution block."""
    docs_directory = "supabase_docs_generated"
    consolidation_threshold = 10000
    
    consolidator = DocsConsolidator(docs_directory, consolidation_threshold)
    consolidator.consolidate()
    print("\n⏹️ Process complete.")


if __name__ == "__main__":
    main() 