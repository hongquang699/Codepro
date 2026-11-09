"""Source code plagiarism and similarity detector using n-gram tokenization."""
import re
from typing import Set, Tuple

class PlagiarismDetector:
    @staticmethod
    def tokenize(code: str) -> Set[str]:
        """Normalizes source code by removing comments, whitespace, and variable names."""
        # Remove comments
        c = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        c = re.sub(r'/\*.*?\*/', '', c, flags=re.DOTALL)
        # Tokenize by keywords and symbols
        tokens = re.findall(r'[a-zA-Z_]\w*|[0-9]+|[^\s\w]', c)
        # Build 3-grams
        ngrams = set()
        for i in range(len(tokens) - 2):
            ngrams.add(f"{tokens[i]}_{tokens[i+1]}_{tokens[i+2]}")
        return ngrams

    @classmethod
    def calculate_similarity(cls, code1: str, code2: str) -> float:
        """Calculates Jaccard similarity index between two code submissions (0.0 to 1.0)."""
        tokens1 = cls.tokenize(code1)
        tokens2 = cls.tokenize(code2)
        if not tokens1 or not tokens2:
            return 0.0
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        return round(intersection / union, 4) if union > 0 else 0.0
