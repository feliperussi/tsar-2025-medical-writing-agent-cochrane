#!/usr/bin/env python3
"""
Text Linguistic Analyzer
Extracts comprehensive linguistic features from text including readability scores,
POS distributions, entity recognition, and stylistic metrics.
"""

import re
import math
import spacy
import readability
import pandas as pd
import json
import argparse
import os
from collections import OrderedDict
from typing import Dict, List, Union, Any

class TextLinguisticAnalyzer:
    """
    Comprehensive text analysis tool for extracting linguistic features
    """

    def __init__(self, spacy_model='en_core_web_lg'):
        """Initialize the analyzer with spaCy model"""
        try:
            self.nlp = spacy.load(spacy_model)
            print(f"Loaded spaCy model: {spacy_model}")
        except OSError:
            print(f"Error: spaCy model '{spacy_model}' not found.")
            print("Install it with: python -m spacy download en_core_web_lg")
            raise

    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex"""
        sentence_enders = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s')
        sentences = sentence_enders.split(text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs on double newlines"""
        paragraphs = re.split(r'\n{2,}', text.strip())
        return [p.strip() for p in paragraphs if p.strip()]

    def count_syllables(self, word: str) -> int:
        """Count syllables in a word using vowel groups heuristic"""
        w = re.sub(r'[^a-z]', '', word.lower())
        if not w:
            return 0
        syllable_groups = re.findall(r'[aeiouy]+', w)
        count = len(syllable_groups)
        # Adjust for trailing 'e'
        if w.endswith('e'):
            count -= 1
        return max(count, 1)

    def get_pos_distributions(self, text: str, include_tokens: bool = False) -> Dict[str, Union[int, List]]:
        """Get part-of-speech and linguistic feature distributions"""
        doc = self.nlp(text)

        def count_pos(pos):
            return len([t for t in doc if t.pos_ == pos])

        def count_tag(tag):
            return len([t for t in doc if t.tag_ == tag])

        def count_dep(dep):
            return len([t for t in doc if t.dep_ == dep])

        def count_entities(ent_type):
            return len([ent for ent in doc.ents if ent.label_ == ent_type])

        def get_tokens_pos(pos):
            return [{"text": t.text, "lemma": t.lemma_, "tag": t.tag_, "dep": t.dep_} for t in doc if t.pos_ == pos]

        def get_tokens_tag(tag):
            return [{"text": t.text, "lemma": t.lemma_, "pos": t.pos_, "dep": t.dep_} for t in doc if t.tag_ == tag]

        def get_tokens_dep(dep):
            return [{"text": t.text, "lemma": t.lemma_, "pos": t.pos_, "tag": t.tag_} for t in doc if t.dep_ == dep]

        def get_entity_tokens(ent_type):
            return [{"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char} for ent in doc.ents if ent.label_ == ent_type]

        result = {
            # Basic counts
            "words": len([t for t in doc if t.pos_ != 'PUNCT']),
            "sentences": len(list(doc.sents)),
            "characters": len(text),

            # Voice analysis
            "passive_voice": count_tag('VBN'),
            "active_voice": count_pos('VERB') - count_tag('VBN'),
            "passive_subjects": count_dep('nsubjpass'),
            "active_subjects": count_dep('nsubj'),

            # Parts of speech
            "verbs": count_pos('VERB'),
            "nouns": count_pos('NOUN'),
            "adjectives": count_pos('ADJ'),
            "adverbs": count_pos('ADV'),
            "prepositions": count_pos('ADP'),
            "auxiliaries": count_pos('AUX'),
            "conjunctions": count_pos('CCONJ') + count_pos('SCONJ'),
            "coord_conjunctions": count_pos('CCONJ'),
            "subordinating_conjunctions": count_pos('SCONJ'),
            "determiners": count_pos('DET'),
            "interjections": count_pos('INTJ'),
            "numbers": count_pos('NUM'),
            "particles": count_pos('PART'),
            "pronouns": count_pos('PRON'),
            "proper_nouns": count_pos('PROPN'),
            "punctuation": count_pos('PUNCT'),
            "symbols": count_pos('SYM'),
            "other": count_pos('X'),

            # Named entities
            "money_entities": count_entities('MONEY'),
            "person_entities": count_entities('PERSON'),
            "norp_entities": count_entities('NORP'),  # Nationalities, religious groups
            "facility_entities": count_entities('FAC'),
            "organization_entities": count_entities('ORG'),
            "gpe_entities": count_entities('GPE'),  # Geopolitical entities
            "product_entities": count_entities('PRODUCT'),
            "event_entities": count_entities('EVENT'),
            "work_of_art_entities": count_entities('WORK_OF_ART'),
            "language_entities": count_entities('LANGUAGE'),
            "date_entities": count_entities('DATE'),
            "time_entities": count_entities('TIME'),
            "quantity_entities": count_entities('QUANTITY'),
            "ordinal_entities": count_entities('ORDINAL'),
            "cardinal_entities": count_entities('CARDINAL'),
            "percent_entities": count_entities('PERCENT'),
            "location_entities": count_entities('LOC'),
            "law_entities": count_entities('LAW'),

            # Stopwords
            "stopwords": len([t for t in doc if t.is_stop]),
        }

        # Add detailed token information if requested
        if include_tokens:
            result["detailed_tokens"] = {
                # Voice analysis tokens
                "passive_voice_tokens": get_tokens_tag('VBN'),
                "active_voice_tokens": [t for t in get_tokens_pos('VERB') if t["tag"] != "VBN"],
                "passive_subject_tokens": get_tokens_dep('nsubjpass'),
                "active_subject_tokens": get_tokens_dep('nsubj'),

                # POS tokens
                "verb_tokens": get_tokens_pos('VERB'),
                "noun_tokens": get_tokens_pos('NOUN'),
                "adjective_tokens": get_tokens_pos('ADJ'),
                "adverb_tokens": get_tokens_pos('ADV'),
                "preposition_tokens": get_tokens_pos('ADP'),
                "auxiliary_tokens": get_tokens_pos('AUX'),
                "coord_conjunction_tokens": get_tokens_pos('CCONJ'),
                "subordinating_conjunction_tokens": get_tokens_pos('SCONJ'),
                "determiner_tokens": get_tokens_pos('DET'),
                "interjection_tokens": get_tokens_pos('INTJ'),
                "number_tokens": get_tokens_pos('NUM'),
                "particle_tokens": get_tokens_pos('PART'),
                "pronoun_tokens": get_tokens_pos('PRON'),
                "proper_noun_tokens": get_tokens_pos('PROPN'),
                "punctuation_tokens": get_tokens_pos('PUNCT'),
                "symbol_tokens": get_tokens_pos('SYM'),
                "other_tokens": get_tokens_pos('X'),

                # Named entity tokens
                "money_entity_tokens": get_entity_tokens('MONEY'),
                "person_entity_tokens": get_entity_tokens('PERSON'),
                "norp_entity_tokens": get_entity_tokens('NORP'),
                "facility_entity_tokens": get_entity_tokens('FAC'),
                "organization_entity_tokens": get_entity_tokens('ORG'),
                "gpe_entity_tokens": get_entity_tokens('GPE'),
                "product_entity_tokens": get_entity_tokens('PRODUCT'),
                "event_entity_tokens": get_entity_tokens('EVENT'),
                "work_of_art_entity_tokens": get_entity_tokens('WORK_OF_ART'),
                "language_entity_tokens": get_entity_tokens('LANGUAGE'),
                "date_entity_tokens": get_entity_tokens('DATE'),
                "time_entity_tokens": get_entity_tokens('TIME'),
                "quantity_entity_tokens": get_entity_tokens('QUANTITY'),
                "ordinal_entity_tokens": get_entity_tokens('ORDINAL'),
                "cardinal_entity_tokens": get_entity_tokens('CARDINAL'),
                "percent_entity_tokens": get_entity_tokens('PERCENT'),
                "location_entity_tokens": get_entity_tokens('LOC'),
                "law_entity_tokens": get_entity_tokens('LAW'),

                # Special categories
                "stopword_tokens": [{"text": t.text, "lemma": t.lemma_, "pos": t.pos_} for t in doc if t.is_stop],
                "all_tokens": [{"text": t.text, "lemma": t.lemma_, "pos": t.pos_, "tag": t.tag_, "dep": t.dep_, "is_stop": t.is_stop} for t in doc]
            }

        return result

    def get_readability_scores(self, text: str) -> Dict[str, Any]:
        """Calculate comprehensive readability metrics"""

        # Get original readability scores for reference
        try:
            orig_scores = readability.getmeasures(text, lang='en')
            orig_sentence_info = dict(orig_scores['sentence info'])
            orig_word_usage = dict(orig_scores['word usage'])
        except:
            orig_sentence_info = {}
            orig_word_usage = {}

        # Get basic counts from POS distributions
        pos_stats = self.get_pos_distributions(text, include_tokens=False)
        num_words = pos_stats["words"]
        num_sentences = pos_stats["sentences"]
        num_characters = pos_stats["characters"]

        # Manual calculations for readability
        paragraphs_list = self.split_paragraphs(text)
        num_paragraphs = len(paragraphs_list)

        # SpaCy tokenization for syllables and complexity
        doc = self.nlp(text)
        alpha_tokens = [t.text for t in doc if t.is_alpha]
        alpha_characters = sum(len(t) for t in alpha_tokens)
        num_syllables = sum(self.count_syllables(t) for t in alpha_tokens)

        # Avoid division by zero
        num_sentences = max(num_sentences, 1)
        num_words = max(num_words, 1)
        num_paragraphs = max(num_paragraphs, 1)

        # Additional metrics
        long_words = sum(1 for t in alpha_tokens if len(t) >= 7)
        polysyllables = sum(1 for t in alpha_tokens if self.count_syllables(t) >= 3)
        complex_words = orig_sentence_info.get("complex_words", polysyllables)
        complex_words_dc = orig_sentence_info.get("complex_words_dc", complex_words)

        # Calculate readability scores
        readability_scores = OrderedDict()

        # Flesch Reading Ease
        if num_words > 0 and num_syllables > 0:
            readability_scores['flesch_reading_ease'] = (
                206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (num_syllables / num_words)
            )

        # Flesch-Kincaid Grade Level
        if num_words > 0 and num_syllables > 0:
            readability_scores['flesch_kincaid_grade'] = (
                0.39 * (num_words / num_sentences) + 11.8 * (num_syllables / num_words) - 15.59
            )

        # Automated Readability Index
        if num_words > 0:
            readability_scores['automated_readability_index'] = (
                4.71 * (alpha_characters / num_words) + 0.5 * (num_words / num_sentences) - 21.43
            )

        # Coleman-Liau Index
        if num_words > 0:
            L = (alpha_characters / num_words) * 100
            S = (num_sentences / num_words) * 100
            readability_scores['coleman_liau_index'] = 0.0588 * L - 0.296 * S - 15.8

        # Gunning Fog Index
        if num_words > 0:
            readability_scores['gunning_fog_index'] = (
                0.4 * ((num_words / num_sentences) + 100 * (complex_words / num_words))
            )

        # LIX (Läsbarhetsindex)
        if num_words > 0:
            readability_scores['lix'] = (long_words / num_words) * 100 + (num_words / num_sentences)

        # SMOG Index
        readability_scores['smog_index'] = 3 + math.sqrt(polysyllables)

        # RIX (Readability Index)
        readability_scores['rix'] = long_words / num_sentences

        # Dale-Chall Readability Score
        if num_words > 0:
            readability_scores['dale_chall_readability'] = (
                0.1579 * ((complex_words_dc / num_words) * 100) + 0.0496 * (num_words / num_sentences)
            )

        # Combine all metrics
        result = readability_scores.copy()
        result.update(pos_stats)

        # Add derived metrics
        if num_words > 0:
            result.update({
                'characters_per_word': alpha_characters / num_words,
                'syllables_per_word': num_syllables / num_words,
                'words_per_sentence': num_words / num_sentences,
                'sentences_per_paragraph': num_sentences / num_paragraphs,
                'type_token_ratio': len(set(alpha_tokens)) / num_words,
                'syllables': num_syllables,
                'paragraphs': num_paragraphs,
                'long_words': long_words,
                'polysyllables': polysyllables,
                'complex_words': complex_words,
                'complex_words_dc': complex_words_dc,
            })

        # Add original library scores if available
        for key in ['tobeverb', 'auxverb', 'conjunction', 'nominalization']:
            if key in orig_word_usage:
                result[key] = orig_word_usage[key]

        if 'wordtypes' in orig_sentence_info:
            result['wordtypes'] = orig_sentence_info['wordtypes']

        return result

    def analyze_text(self, text: str, include_tokens: bool = False) -> Dict[str, Any]:
        """
        Perform comprehensive linguistic analysis on text

        Args:
            text (str): Input text to analyze
            include_tokens (bool): Whether to include detailed token information

        Returns:
            Dict containing all linguistic features and readability scores
        """
        if not text or not text.strip():
            return {"error": "Empty or invalid text provided"}

        try:
            results = self.get_readability_scores(text)

            # Add detailed token information if requested
            if include_tokens:
                detailed_pos = self.get_pos_distributions(text, include_tokens=True)
                if "detailed_tokens" in detailed_pos:
                    results["detailed_tokens"] = detailed_pos["detailed_tokens"]

            # Add metadata
            results['analysis_metadata'] = {
                'text_length': len(text),
                'text_preview': text[:100] + "..." if len(text) > 100 else text,
                'analysis_timestamp': pd.Timestamp.now().isoformat(),
                'includes_detailed_tokens': include_tokens
            }

            return results

        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

    def analyze_multiple_texts(self, texts: List[str], text_ids: List[str] = None, include_tokens: bool = False) -> List[Dict[str, Any]]:
        """
        Analyze multiple texts

        Args:
            texts (List[str]): List of texts to analyze
            text_ids (List[str], optional): IDs for each text
            include_tokens (bool): Whether to include detailed token information

        Returns:
            List of analysis results
        """
        if text_ids is None:
            text_ids = [f"text_{i+1}" for i in range(len(texts))]

        results = []
        for i, text in enumerate(texts):
            result = self.analyze_text(text, include_tokens=include_tokens)
            result['text_id'] = text_ids[i] if i < len(text_ids) else f"text_{i+1}"
            results.append(result)

        return results

    def analyze_csv(self, csv_file: str, text_column: str, id_column: str = None, include_tokens: bool = False) -> List[Dict[str, Any]]:
        """
        Analyze texts from a CSV file

        Args:
            csv_file (str): Path to CSV file
            text_column (str): Name of column containing text
            id_column (str, optional): Name of column containing IDs
            include_tokens (bool): Whether to include detailed token information

        Returns:
            List of analysis results
        """
        try:
            df = pd.read_csv(csv_file)

            if text_column not in df.columns:
                raise ValueError(f"Column '{text_column}' not found in CSV")

            texts = df[text_column].fillna("").astype(str).tolist()

            if id_column and id_column in df.columns:
                text_ids = df[id_column].astype(str).tolist()
            else:
                text_ids = None

            return self.analyze_multiple_texts(texts, text_ids, include_tokens=include_tokens)

        except Exception as e:
            return [{"error": f"CSV analysis failed: {str(e)}"}]

def main():
    parser = argparse.ArgumentParser(description='Analyze linguistic features of text')
    parser.add_argument('--text', type=str, help='Single text to analyze')
    parser.add_argument('--file', type=str, help='Text file to analyze')
    parser.add_argument('--csv', type=str, help='CSV file to analyze')
    parser.add_argument('--text-column', type=str, default='text',
                       help='Column name containing text (for CSV)')
    parser.add_argument('--id-column', type=str,
                       help='Column name containing IDs (for CSV)')
    parser.add_argument('--output', type=str, help='Output JSON file')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    parser.add_argument('--include-tokens', action='store_true',
                       help='Include detailed token information for each category')

    args = parser.parse_args()

    if not any([args.text, args.file, args.csv]):
        print("Error: Provide --text, --file, or --csv")
        return 1

    # Initialize analyzer
    try:
        analyzer = TextLinguisticAnalyzer()
    except Exception as e:
        print(f"Error initializing analyzer: {e}")
        return 1

    # Perform analysis
    results = None

    if args.text:
        print("Analyzing single text...")
        results = analyzer.analyze_text(args.text, include_tokens=args.include_tokens)

    elif args.file:
        print(f"Analyzing text file: {args.file}")
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            return 1

        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
        results = analyzer.analyze_text(text, include_tokens=args.include_tokens)

    elif args.csv:
        print(f"Analyzing CSV file: {args.csv}")
        if not os.path.exists(args.csv):
            print(f"Error: CSV file not found: {args.csv}")
            return 1

        results = analyzer.analyze_csv(args.csv, args.text_column, args.id_column, include_tokens=args.include_tokens)

    # Output results
    if results:
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2 if args.pretty else None, ensure_ascii=False)
            print(f"Results saved to: {args.output}")
        else:
            print(json.dumps(results, indent=2 if args.pretty else None, ensure_ascii=False))

    return 0

if __name__ == "__main__":
    exit(main())
