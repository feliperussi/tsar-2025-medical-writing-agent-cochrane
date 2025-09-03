import os
import re
import torch
from tqdm import tqdm
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class AlignScoreEvaluator:
    def __init__(self, model_name="krotima1/AlignScoreCS", device=None):
        """
        Initialize AlignScore evaluator.
        
        Args:
            model_name: HuggingFace model name for AlignScore
            device: Device to use (if None, auto-detect MPS/CPU)
        """
        if device is None:
            self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"AlignScore using device: {self.device}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()
    
    def split_text_into_chunks(self, text, chunk_size_tokens=350):
        """Split a text into chunks of ~350 tokens each (subwords)."""
        tokens = self.tokenizer.tokenize(text)
        chunks = []
        for i in range(0, len(tokens), chunk_size_tokens):
            chunk_tokens = tokens[i : i + chunk_size_tokens]
            chunk_text = self.tokenizer.convert_tokens_to_string(chunk_tokens)
            chunks.append(chunk_text)
        return chunks
    
    def split_into_sentences(self, claim_text):
        """Split the claim into sentences in a simple way."""
        claim_text = claim_text.strip()
        sentences = re.split(r'(?<=[.?!])\s+', claim_text)
        return [s.strip() for s in sentences if s.strip()]
    
    def score_pair(self, context_piece, claim_piece):
        """Return the 'consistency probability' between a context piece and a claim sentence."""
        inputs = self.tokenizer(
            context_piece, claim_piece, 
            return_tensors="pt",
            truncation=True, 
            padding=True, 
            max_length=512
        )
        
        # Move tensors to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)
        
        # Class 1 corresponds to "positive consistency"
        return probs[0, 1].item()
    
    def align_score(self, context, claim, chunk_size_tokens=350):
        """
        Implement the AlignScore logic:
        1) Split the context into chunks of ~350 tokens
        2) Split the claim into sentences
        3) For each sentence, evaluate in all chunks and take the maximum score
        4) Average the maximum scores of each sentence -> final AlignScore
        """
        context_chunks = self.split_text_into_chunks(context, chunk_size_tokens=chunk_size_tokens)
        claim_sentences = self.split_into_sentences(claim)
        
        if not claim_sentences:
            return 0.0
        
        sentence_scores = []
        for sentence in claim_sentences:
            chunk_scores = [self.score_pair(chunk, sentence) for chunk in context_chunks]
            max_score = max(chunk_scores) if chunk_scores else 0.0
            sentence_scores.append(max_score)
        
        return sum(sentence_scores) / len(sentence_scores)
    
    def evaluate_consistency(self, context, claim):
        """Evaluate factual consistency using AlignScore logic for a (context, claim)."""
        return self.align_score(context, claim, chunk_size_tokens=350)


def get_alignscore(predictions, references, evaluator=None):
    """
    Calculate AlignScore for a list of predictions and references.
    
    Args:
        predictions: List of prediction texts (claims)
        references: List of reference texts (contexts)
        evaluator: AlignScoreEvaluator instance (if None, creates a new one)
    
    Returns:
        Mean AlignScore rounded to 4 decimal places
    """
    assert len(predictions) == len(references), "The number of references is different from the number of predictions."
    
    if evaluator is None:
        evaluator = AlignScoreEvaluator()
    
    scores = []
    for pred, ref in tqdm(zip(predictions, references), total=len(predictions), desc="Computing AlignScore"):
        score = evaluator.evaluate_consistency(ref, pred)  # ref is context, pred is claim
        scores.append(score)
    
    return round(sum(scores) / len(scores), 4)