#!/usr/bin/env python3
"""
Supabase Documentation Index Generator

This script reads the Supabase Python reference documentation and creates
a comprehensive index of all sections, methods, and topics.
"""

import re
from typing import List, Dict, Tuple
from pathlib import Path


class SupabaseDocsIndexer:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.content = ""
        self.index = {}
        
    def read_file(self):
        """Read the documentation file"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
        except FileNotFoundError:
            print(f"Error: File {self.file_path} not found")
            return False
        return True
    
    def extract_sections(self) -> List[Tuple[str, int]]:
        """Extract all section headers and their line numbers"""
        lines = self.content.split('\n')
        sections = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for main section headers (# Python Reference)
            if line == '# Python Reference':
                # Look for the next non-empty line that contains the topic
                j = i + 1
                while j < len(lines) and j < i + 10:  # Look within next 10 lines
                    candidate = lines[j].strip()
                    # Skip empty lines and markdown headers
                    if candidate and not candidate.startswith('#') and not candidate.startswith('```'):
                        # This is likely our section title
                        sections.append((candidate, j + 1))
                        break
                    j += 1
                else:
                    # If we can't find a title, use "Overview"
                    sections.append(("Overview", i + 1))
            
            i += 1
        
        return sections
    
    def categorize_sections(self, sections: List[Tuple[str, int]]) -> Dict[str, List[Tuple[str, int]]]:
        """Categorize sections into logical groups"""
        categories = {
            "Client Setup": [],
            "Database Operations": [],
            "Filters": [],
            "Modifiers": [],
            "Authentication": [],
            "Multi-Factor Authentication": [],
            "Admin Functions": [],
            "Edge Functions": [],
            "Realtime": [],
            "Storage": [],
            "Utilities": []
        }
        
        # Define patterns for categorization
        database_ops = ['select()', 'insert()', 'update()', 'upsert()', 'delete()', 'rpc()']
        filters = ['eq()', 'neq()', 'gt()', 'gte()', 'lt()', 'lte()', 'like()', 'ilike()', 
                  'is_()', 'in_()', 'contains()', 'contained_by()', 'range_gt()', 'range_gte()',
                  'range_lt()', 'range_lte()', 'range_adjacent()', 'overlaps()', 'text_search()',
                  'match()', 'not_()', 'or_()', 'filter()', 'Using Filters']
        modifiers = ['order()', 'limit()', 'range()', 'single()', 'maybe_single()', 'csv()', 
                    'Using Modifiers', 'Using Explain']
        auth = ['sign_up()', 'sign_in_anonymously()', 'sign_in_with_password', 'sign_in_with_id_token',
                'sign_in_with_otp', 'sign_in_with_oauth', 'sign_in_with_sso()', 'sign_out()',
                'reset_password_for_email()', 'verify_otp', 'get_session', 'refresh_session()',
                'get_user', 'update_user()', 'get_user_identities()', 'link_identity()',
                'unlink_identity()', 'reauthenticate()', 'resend()', 'set_session()',
                'exchange_code_for_session()']
        mfa = ['mfa.enroll()', 'mfa.challenge()', 'mfa.verify()', 'mfa.challenge_and_verify()',
               'mfa.unenroll()', 'mfa.get_authenticator_assurance_level()']
        admin = ['get_user_by_id()', 'list_users()', 'create_user()', 'delete_user()',
                'invite_user_by_email()', 'generate_link()', 'update_user_by_id()', 'mfa.delete_factor()']
        functions = ['invoke()']
        realtime = ['on().subscribe()', 'removeChannel()', 'removeAllChannels()', 'getChannels()',
                   'broadcastMessage()', 'acreate_client()']
        storage = ['create_bucket()', 'get_bucket()', 'list_buckets()', 'update_bucket()',
                  'delete_bucket()', 'empty_bucket()', 'from_.upload()', 'from_.download()',
                  'from_.list()', 'from_.update()', 'from_.move()', 'from_.copy()',
                  'from_.remove()', 'from_.create_signed_url()', 'from_.create_signed_urls()',
                  'from_.create_signed_upload_url()', 'from_.upload_to_signed_url()',
                  'from_.get_public_url()']
        
        for section, line_num in sections:
            categorized = False
            
            # Check if it's a client setup section
            if 'create_client' in section or section in ['Overview'] and line_num < 100:
                categories["Client Setup"].append((section, line_num))
                categorized = True
            # Check database operations
            elif any(op in section for op in database_ops):
                categories["Database Operations"].append((section, line_num))
                categorized = True
            # Check filters
            elif any(filt in section for filt in filters):
                categories["Filters"].append((section, line_num))
                categorized = True
            # Check modifiers
            elif any(mod in section for mod in modifiers):
                categories["Modifiers"].append((section, line_num))
                categorized = True
            # Check MFA first (more specific)
            elif any(mfa_item in section for mfa_item in mfa):
                categories["Multi-Factor Authentication"].append((section, line_num))
                categorized = True
            # Check admin functions
            elif any(admin_item in section for admin_item in admin) or 'admin' in section.lower():
                categories["Admin Functions"].append((section, line_num))
                categorized = True
            # Check auth (after MFA and admin checks)
            elif any(auth_item in section for auth_item in auth):
                categories["Authentication"].append((section, line_num))
                categorized = True
            # Check functions
            elif any(func in section for func in functions):
                categories["Edge Functions"].append((section, line_num))
                categorized = True
            # Check realtime
            elif any(rt in section for rt in realtime) or 'realtime' in section.lower():
                categories["Realtime"].append((section, line_num))
                categorized = True
            # Check storage
            elif any(stor in section for stor in storage) or 'storage' in section.lower():
                categories["Storage"].append((section, line_num))
                categorized = True
            
            # If not categorized, put in utilities
            if not categorized:
                categories["Utilities"].append((section, line_num))
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def generate_index(self):
        """Generate the complete index"""
        if not self.read_file():
            return
        
        sections = self.extract_sections()
        categorized = self.categorize_sections(sections)
        
        print("=" * 60)
        print("SUPABASE PYTHON REFERENCE - DOCUMENTATION INDEX")
        print("=" * 60)
        print(f"Total sections found: {len(sections)}")
        print()
        
        for category, items in categorized.items():
            if items:
                print(f"📁 {category.upper()}")
                print("-" * 40)
                for item, line_num in sorted(items, key=lambda x: x[1]):
                    print(f"   • {item:<35} (Line {line_num})")
                print()
        
        # Generate summary statistics
        print("📊 SUMMARY STATISTICS")
        print("-" * 40)
        for category, items in categorized.items():
            if items:
                print(f"   {category}: {len(items)} sections")
        print()
        
        # Generate quick reference for common operations
        print("🚀 QUICK REFERENCE - COMMON OPERATIONS")
        print("-" * 40)
        common_ops = [
            ("Create client", "create_client()"),
            ("Select data", "select()"),
            ("Insert data", "insert()"),
            ("Update data", "update()"),
            ("Delete data", "delete()"),
            ("Sign up user", "sign_up()"),
            ("Sign in user", "sign_in_with_password"),
            ("Upload file", "from_.upload()"),
            ("Download file", "from_.download()"),
        ]
        
        for desc, method in common_ops:
            # Find the method in our sections
            found = False
            for category, items in categorized.items():
                for item, line_num in items:
                    if method in item:
                        print(f"   • {desc:<20} → {method:<25} (Line {line_num})")
                        found = True
                        break
                if found:
                    break
        
        print("\n" + "=" * 60)


def main():
    """Main function to run the indexer"""
    # Look for the Supabase documentation file
    doc_file = "references/supabase_llms_full_like.txt"
    
    if not Path(doc_file).exists():
        print(f"Error: Documentation file '{doc_file}' not found.")
        print("Please make sure the file exists in the references/ directory.")
        return
    
    indexer = SupabaseDocsIndexer(doc_file)
    indexer.generate_index()


if __name__ == "__main__":
    main() 