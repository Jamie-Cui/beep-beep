from typing import List, Dict, Set
import re


class KeywordFilter:
    """Filters papers based on keyword matching for security/crypto + LLM topics."""

    # Keywords related to security and cryptography
    SECURITY_CRYPTO_KEYWORDS = {
        'security', 'secure', 'cryptography', 'cryptographic', 'encryption',
        'decrypt', 'cipher', 'authentication', 'privacy', 'private',
        'adversarial', 'attack', 'defense', 'vulnerability', 'threat',
        'zero-knowledge', 'zkp', 'homomorphic', 'differential privacy',
        'backdoor', 'trojan', 'malware', 'exploit', 'penetration',
        'intrusion', 'firewall', 'blockchain', 'smart contract',
        'post-quantum', 'lattice', 'hash', 'signature', 'key exchange',
        'tls', 'ssl', 'pki', 'certificate', 'quantum resistant',
        'side-channel', 'timing attack', 'fault injection', 'rop',
        'control flow', 'memory safety', 'sandbox', 'isolation'
    }

    # Keywords related to LLMs and AI
    LLM_AI_KEYWORDS = {
        'llm', 'large language model', 'language model', 'gpt', 'bert',
        'transformer', 'attention', 'neural network', 'deep learning',
        'machine learning', 'ai', 'artificial intelligence', 'nlp',
        'natural language processing', 'generative', 'chatbot', 'chat',
        'prompt', 'fine-tuning', 'pre-training', 'embedding', 'token',
        'reasoning', 'agent', 'foundation model', 'multimodal',
        'retrieval augmented', 'rag', 'in-context learning', 'few-shot',
        'zero-shot', 'instruction tuning', 'alignment', 'rlhf',
        'code generation', 'copilot', 'llama', 'claude', 'palm',
        'gemini', 'mistral', 'mixtral', 'diffusion', 'stable diffusion',
        'generative ai', 'genai'
    }

    def __init__(self, require_both_categories: bool = True, min_keyword_score: int = 2):
        """
        Initialize keyword filter.

        Args:
            require_both_categories: If True, papers must match keywords from both
                                    security/crypto AND LLM/AI categories
            min_keyword_score: Minimum number of keyword matches required
        """
        self.require_both_categories = require_both_categories
        self.min_keyword_score = min_keyword_score
        # Create instance copies of keyword sets
        self.security_crypto_keywords = self.SECURITY_CRYPTO_KEYWORDS.copy()
        self.llm_ai_keywords = self.LLM_AI_KEYWORDS.copy()

    def filter_papers(self, papers: List[Dict]) -> List[Dict]:
        """
        Filter papers based on keyword matching.

        Args:
            papers: List of paper dictionaries

        Returns:
            Filtered list of papers with added 'keywords' field
        """
        filtered = []

        for paper in papers:
            # Combine title and abstract for keyword matching
            text = f"{paper['title']} {paper['abstract']}".lower()

            # Find matching keywords
            security_matches = self._find_matches(text, self.security_crypto_keywords)
            llm_matches = self._find_matches(text, self.llm_ai_keywords)

            # Calculate scores
            security_score = len(security_matches)
            llm_score = len(llm_matches)
            total_score = security_score + llm_score

            # Apply filtering logic
            if self.require_both_categories:
                # Must have matches in both categories
                if security_score >= 1 and llm_score >= 1 and total_score >= self.min_keyword_score:
                    paper['keywords'] = list(security_matches | llm_matches)
                    paper['keyword_score'] = total_score
                    filtered.append(paper)
            else:
                # Just need minimum total score
                if total_score >= self.min_keyword_score:
                    paper['keywords'] = list(security_matches | llm_matches)
                    paper['keyword_score'] = total_score
                    filtered.append(paper)

        print(f"Filtered {len(filtered)} papers out of {len(papers)} (matched keywords)")
        return filtered

    def _find_matches(self, text: str, keywords: Set[str]) -> Set[str]:
        """
        Find keyword matches in text.

        Args:
            text: Text to search (lowercase)
            keywords: Set of keywords to search for

        Returns:
            Set of matched keywords
        """
        matches = set()

        for keyword in keywords:
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                matches.add(keyword)

        return matches

    def add_custom_keywords(self, security_keywords: List[str] = None,
                           llm_keywords: List[str] = None):
        """
        Add custom keywords to the filter.

        Args:
            security_keywords: Additional security/crypto keywords
            llm_keywords: Additional LLM/AI keywords
        """
        if security_keywords:
            self.security_crypto_keywords.update(k.lower() for k in security_keywords)
        if llm_keywords:
            self.llm_ai_keywords.update(k.lower() for k in llm_keywords)
