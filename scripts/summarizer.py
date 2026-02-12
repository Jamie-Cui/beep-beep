import requests
import time
from typing import Dict, Optional


class ModelScopeSummarizer:
    """Summarizes paper abstracts using ModelScope API."""

    API_URL = "https://api-inference.modelscope.cn/api/v1/models/{model}/text-generation"
    DEFAULT_MODEL = "Qwen/Qwen2.5-72B-Instruct"  # Free model on ModelScope
    DEFAULT_MAX_TOKENS = 300
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_TIMEOUT = 60
    DEFAULT_RATE_LIMIT_DELAY = 1.0

    def __init__(self, api_key: str, model: str = None, max_retries: int = 3, retry_delay: float = 5.0):
        """
        Initialize ModelScope summarizer.

        Args:
            api_key: ModelScope API key
            model: Model name to use (default: Qwen2.5-72B-Instruct)
            max_retries: Maximum number of retry attempts for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def summarize(self, paper: Dict) -> Optional[str]:
        """
        Generate a summary for a paper.

        Args:
            paper: Paper dictionary containing title and abstract

        Returns:
            Summary text, or None if summarization fails
        """
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')

        if not abstract:
            print(f"No abstract for paper: {title[:50]}...")
            return None

        # Create prompt for summarization
        prompt = self._create_prompt(title, abstract)

        # Try to generate summary with retries
        for attempt in range(self.max_retries):
            try:
                summary = self._call_api(prompt)
                if summary:
                    return summary
            except Exception as e:
                print(f"Attempt {attempt + 1}/{self.max_retries} failed for paper '{title[:50]}...': {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)

        return None

    def _create_prompt(self, title: str, abstract: str) -> str:
        """
        Create a prompt for the summarization model.

        Args:
            title: Paper title
            abstract: Paper abstract

        Returns:
            Formatted prompt
        """
        return f"""Summarize the following research paper in 3-5 sentences. Focus on the main contribution, methods, and results.

Title: {title}

Abstract: {abstract}

Summary:"""

    def _call_api(self, prompt: str) -> Optional[str]:
        """
        Call ModelScope API to generate summary.

        Args:
            prompt: The prompt to send to the model

        Returns:
            Generated summary, or None if failed
        """
        url = self.API_URL.format(model=self.model)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "max_tokens": self.DEFAULT_MAX_TOKENS,
                "temperature": self.DEFAULT_TEMPERATURE
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.DEFAULT_TIMEOUT)
            response.raise_for_status()

            result = response.json()

            # Extract summary from response
            if "output" in result and "choices" in result["output"]:
                choices = result["output"]["choices"]
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    content = message.get("content", "").strip()
                    if content:
                        return content

            print(f"Unexpected API response format: {result}")
            return None

        except requests.RequestException as e:
            print(f"API request failed: {e}")
            raise
        except Exception as e:
            print(f"Error processing API response: {e}")
            raise

    def batch_summarize(self, papers: list, delay: float = None) -> tuple:
        """
        Summarize multiple papers with rate limiting.

        Args:
            papers: List of paper dictionaries
            delay: Delay between API calls to avoid rate limiting (default: DEFAULT_RATE_LIMIT_DELAY)

        Returns:
            Tuple of (successful_papers, failed_papers)
        """
        if delay is None:
            delay = self.DEFAULT_RATE_LIMIT_DELAY

        successful = []
        failed = []

        total = len(papers)
        for i, paper in enumerate(papers, 1):
            print(f"Summarizing paper {i}/{total}: {paper['title'][:60]}...")

            summary = self.summarize(paper)

            if summary:
                paper['summary'] = summary
                paper['summary_status'] = 'success'
                successful.append(paper)
            else:
                paper['summary'] = paper.get('abstract', '')  # Fallback to abstract
                paper['summary_status'] = 'failed'
                failed.append(paper)

            # Rate limiting
            if i < total:
                time.sleep(delay)

        print(f"Summarization complete: {len(successful)} successful, {len(failed)} failed")
        return successful, failed
