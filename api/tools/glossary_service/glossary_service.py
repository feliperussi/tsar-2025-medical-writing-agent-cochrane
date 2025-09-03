import json
import os
import re
from collections import defaultdict
from typing import List, Dict, Any, Set

class GlossaryService:
    """
    Loads and indexes multiple glossaries to provide an efficient service 
    for finding and defining complex medical phrases within a body of text.
    """
    
    def __init__(self, glossaries_dir: str):
        """Initializes the service by loading and indexing all glossaries."""
        self.phrase_index: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.all_known_phrases: Set[str] = set()
        self._load_and_index(glossaries_dir)
        print(f"GlossaryService is ready. Indexed {len(self.all_known_phrases)} unique phrases and their aliases.")

    def _generate_aliases(self, term: str) -> Set[str]:
        """
        Generates a set of possible aliases for a given term.
        Example: "Pertussis (Whooping Cough)" -> {"pertussis (whooping cough)", "pertussis", "whooping cough"}
        """
        aliases = set()
        # Normalize to lowercase
        lower_term = term.lower()
        aliases.add(lower_term)

        # Handle terms in parentheses, e.g., "Term (Alias)"
        parentheses_match = re.search(r'(.+)\s\((.+)\)', lower_term)
        if parentheses_match:
            main_part = parentheses_match.group(1).strip()
            alias_part = parentheses_match.group(2).strip()
            aliases.add(main_part)
            aliases.add(alias_part)
        
        return aliases

    def _load_and_index(self, glossaries_dir: str):
        """
        Loads all JSON files, enriches entries with their source, 
        generates aliases, and builds the phrase index.
        """
        for filename in os.listdir(glossaries_dir):
            if filename.endswith('.json'):
                source_name = filename.replace('.json', '')
                filepath = os.path.join(glossaries_dir, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data:
                        original_term = entry.get("term", "")
                        if not original_term:
                            continue

                        definition_record = {
                            "main_term": original_term,
                            "plain_alternative": entry["plain_alternative"],
                            "source": source_name
                        }
                        
                        # Generate and index all aliases for the term
                        aliases = self._generate_aliases(original_term)
                        for alias in aliases:
                            self.phrase_index[alias].append(definition_record)
                        
                        self.all_known_phrases.update(aliases)

    def find_and_define_phrases_in_text(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        The main tool for the agent. Finds all known glossary phrases within a
        given text and returns them with their definitions. It searches for 
        the longest possible phrases first to ensure maximum specificity.
        """
        found_phrases = {}
        text_lower = text.lower()
        
        # We sort known phrases by length (descending) to match longest phrases first
        # This prevents "disease" from being matched if "chronic disease" is present.
        sorted_phrases = sorted(list(self.all_known_phrases), key=len, reverse=True)
        
        text_to_scan = text_lower
        
        for phrase in sorted_phrases:
            # Use regex to find whole-word matches only
            if re.search(r'\b' + re.escape(phrase) + r'\b', text_to_scan):
                # We found a match. Add it to our results.
                found_phrases[phrase] = self.phrase_index[phrase]
                
                # To prevent sub-phrases from being matched, we can replace the found
                # phrase in our temporary text. This is a simple way to handle overlaps.
                text_to_scan = text_to_scan.replace(phrase, "")
                
        return found_phrases

    def find_and_define_phrases_in_text_enhanced(self, text: str) -> Dict[str, Any]:
        """
        Enhanced version that returns detailed match information including:
        - Location of each match (start/end positions)
        - The specific alias that triggered the match
        - Grouped by main term with all definitions
        """
        found_terms = {}
        text_lower = text.lower()
        original_text = text
        
        # Track which parts of the text have been matched to avoid overlaps
        matched_ranges = []
        
        # Sort phrases by length (descending) to match longest phrases first
        sorted_phrases = sorted(list(self.all_known_phrases), key=len, reverse=True)
        
        for phrase in sorted_phrases:
            # Find all matches of this phrase in the text
            pattern = r'\b' + re.escape(phrase) + r'\b'
            for match in re.finditer(pattern, text_lower):
                start_pos = match.start()
                end_pos = match.end()
                
                # Check if this match overlaps with any existing matches
                if any(start_pos < existing_end and end_pos > existing_start 
                      for existing_start, existing_end in matched_ranges):
                    continue
                
                # Get the definitions for this phrase
                definitions = self.phrase_index[phrase]
                
                # Group by main_term
                for definition in definitions:
                    main_term = definition["main_term"]
                    
                    if main_term not in found_terms:
                        found_terms[main_term] = {
                            "main_term": main_term,
                            "definitions": [],
                            "matches_in_text": []
                        }
                    
                    # Add definition if not already present
                    def_info = {
                        "plain_alternative": definition["plain_alternative"],
                        "source": definition["source"]
                    }
                    if def_info not in found_terms[main_term]["definitions"]:
                        found_terms[main_term]["definitions"].append(def_info)
                    
                    # Add match location
                    match_info = {
                        "alias_found": original_text[start_pos:end_pos],
                        "location_start": start_pos,
                        "location_end": end_pos
                    }
                    if match_info not in found_terms[main_term]["matches_in_text"]:
                        found_terms[main_term]["matches_in_text"].append(match_info)
                
                # Mark this range as matched
                matched_ranges.append((start_pos, end_pos))
        
        # Convert to the desired output format
        result = {
            "analysis_summary": {
                "total_unique_phrases_found": len(found_terms),
                "text_character_length": len(text)
            },
            "found_terms": list(found_terms.values())
        }
        
        return result

# --- How to use it in your test file ---
#
# if __name__ == "__main__":
#     # 1. Point to the directory with your 11 JSON files
#     glossary_service = GlossaryService(glossaries_dir='./glossaries')
#
#     # 2. Analyze a text
#     text_to_analyze = "The patient experienced adverse effects during the clinical trial and was later diagnosed with Oral Poliovirus (OPV)."
#
#     # 3. Use the new, powerful method
#     complex_phrases_report = glossary_service.find_and_define_phrases_in_text(text_to_analyze)
#
#     # 4. Print the report
#     import pprint
#     pprint.pprint(complex_phrases_report)