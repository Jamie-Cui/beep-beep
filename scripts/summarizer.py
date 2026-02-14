import requests
import time
from typing import Dict, Optional
import sys
import os

# Import progress utilities if available
try:
    from progress import ProgressBar

    HAS_PROGRESS = True
except ImportError:
    HAS_PROGRESS = False


class ModelScopeSummarizer:
    """Summarizes paper abstracts using DashScope API (Qwen/通义千问)."""

    # DashScope API (阿里云通义千问)
    API_URL = (
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    )
    DEFAULT_MODEL = "qwen-plus"  # Free tier available
    DEFAULT_MAX_TOKENS = 500
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_TIMEOUT = 60
    DEFAULT_RATE_LIMIT_DELAY = 1.0

    def __init__(
        self,
        api_key: str,
        model: str = None,
        max_retries: int = 3,
        retry_delay: float = 5.0,
    ):
        """
        Initialize DashScope summarizer.

        Args:
            api_key: DashScope API key (from https://dashscope.console.aliyun.com/)
            model: Model name to use (default: qwen-plus)
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
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")

        if not abstract:
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
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)

        return None

    def _create_prompt(self, title: str, abstract: str) -> str:
        """Create a prompt for the summarization model."""
        return f"""你是一位精通各领域前沿研究的学术文献解读专家，面对一篇给定的论文，请你高效阅读并迅速提取出其核心内容。要求在解读过程中，先对文献的背景、研究目的和问题进行简明概述，再详细梳理研究方法、关键数据、主要发现及结论，同时对新颖概念进行通俗易懂的解释，帮助读者理解论文的逻辑与创新点；最后，请对文献的优缺点进行客观评价，并指出可能的后续研究方向。整体报告结构清晰、逻辑严谨。

Title: {title}

Abstract: {abstract}

Provide a concise summary:"""

    def _call_api(self, prompt: str) -> Optional[str]:
        """Call DashScope API to generate summary."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "parameters": {
                "max_tokens": self.DEFAULT_MAX_TOKENS,
                "temperature": self.DEFAULT_TEMPERATURE,
                "result_format": "message",
            },
        }

        try:
            response = requests.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=self.DEFAULT_TIMEOUT,
            )
            response.raise_for_status()

            result = response.json()

            # Extract summary from DashScope response format
            if "output" in result and "choices" in result["output"]:
                choices = result["output"]["choices"]
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    content = message.get("content", "").strip()
                    if content:
                        return content

            return None

        except requests.RequestException as e:
            raise

    def batch_summarize(self, papers: list, delay: float = None) -> tuple:
        """
        Summarize multiple papers with rate limiting and progress display.

        Args:
            papers: List of paper dictionaries
            delay: Delay between API calls to avoid rate limiting

        Returns:
            Tuple of (successful_papers, failed_papers)
        """
        if delay is None:
            delay = self.DEFAULT_RATE_LIMIT_DELAY

        successful = []
        failed = []
        total = len(papers)

        # Create progress bar if available
        if HAS_PROGRESS:
            progress = ProgressBar(total, "Summarizing papers")
        else:
            progress = None

        for i, paper in enumerate(papers, 1):
            # Update progress bar or print simple progress
            if progress:
                progress.update(1)
            else:
                print(f"[{i}/{total}] Summarizing: {paper['title'][:60]}...")

            summary = self.summarize(paper)

            if summary:
                paper["summary"] = summary
                paper["summary_status"] = "success"
                successful.append(paper)
            else:
                abstract = paper.get("abstract", "")
                if abstract:
                    paper["summary"] = abstract
                else:
                    paper["summary"] = "Summary not available"
                paper["summary_status"] = "failed"
                failed.append(paper)

            # Rate limiting
            if i < total:
                time.sleep(delay)

        # Finish progress bar
        if progress:
            progress.finish()

        print(
            f"\n✓ Summarization complete: {len(successful)} successful, {len(failed)} failed"
        )
        return successful, failed
