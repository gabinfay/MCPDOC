#!/usr/bin/env python3
"""
Documentation Structure Analyzer

This script analyzes a directory of generated documentation files to provide
insights into its structure, such as file counts, line counts, and token counts
per category. This helps in deciding which categories should be consolidated.
"""
import os
from pathlib import Path
import tiktoken
from typing import Dict, Any


class DocsAnalyzer:
    """Analyzes the structure of a documentation folder."""

    def __init__(self, docs_dir: str):
        self.docs_dir = Path(docs_dir)
        if not self.docs_dir.is_dir():
            raise FileNotFoundError(f"Documentation directory not found: '{docs_dir}'")
        
        # Initialize tokenizer for gpt-2, which is a good default for token counting
        # as it's fast and the ratios are similar to more complex models.
        try:
            self.tokenizer = tiktoken.get_encoding("gpt2")
        except Exception:
            # Fallback for environments where the full registry isn't available
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")

    def analyze_structure(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyzes each category subdirectory for file count, line count, and
        token count.
        """
        analysis_results = {}
        
        for category_path in self.docs_dir.iterdir():
            if not category_path.is_dir():
                continue
            
            category_name = category_path.name
            category_stats = {
                "file_count": 0,
                "total_lines": 0,
                "total_tokens": 0,
                "file_details": []
            }

            for file_path in category_path.glob("*.md"):
                content = file_path.read_text(encoding='utf-8')
                lines = content.splitlines()
                tokens = self.tokenizer.encode(content)
                
                category_stats["file_count"] += 1
                category_stats["total_lines"] += len(lines)
                category_stats["total_tokens"] += len(tokens)
                category_stats["file_details"].append({
                    "name": file_path.name,
                    "lines": len(lines),
                    "tokens": len(tokens)
                })

            analysis_results[category_name] = category_stats
        
        return analysis_results

    @staticmethod
    def print_analysis_report(results: Dict[str, Dict[str, Any]]):
        """Prints a formatted report of the analysis."""
        print("=" * 60)
        print("Documentation Structure Analysis Report")
        print("=" * 60)
        
        # Sort categories by total token count for easier review
        sorted_categories = sorted(results.items(), key=lambda item: item[1]['total_tokens'])
        
        for category_name, stats in sorted_categories:
            print(f"\n📁 Category: {category_name}")
            print("-" * 40)
            print(f"  - Total Files:  {stats['file_count']}")
            print(f"  - Total Lines:  {stats['total_lines']:,}")
            print(f"  - Total Tokens: {stats['total_tokens']:,}")
            
            # Show details for the 3 largest files in the category
            if stats['file_details']:
                print("  - Largest files in this category:")
                largest_files = sorted(stats['file_details'], key=lambda x: x['tokens'], reverse=True)[:3]
                for f_detail in largest_files:
                    print(f"    - {f_detail['name']}: {f_detail['tokens']:,} tokens")

        print("\n" + "=" * 60)
        print("This report helps decide which categories to merge into single files.")
        print("Low token count categories are good candidates for consolidation.")


def main():
    """Main execution block."""
    docs_directory = "supabase_docs_generated"
    
    print(f"▶️ Analyzing documentation structure in '{docs_directory}'...")
    
    try:
        analyzer = DocsAnalyzer(docs_directory)
        results = analyzer.analyze_structure()
        analyzer.print_analysis_report(results)
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Please run the `unflatten_docs.py` script first to generate the documentation folder.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main() 