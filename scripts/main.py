#!/usr/bin/env python3
"""
Main script for fetching, filtering, and summarizing papers from arXiv and IACR.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fetchers.arxiv import ArxivFetcher
from fetchers.iacr import IACRFetcher
from filter import KeywordFilter
from summarizer import ModelScopeSummarizer

# Import progress utilities
try:
    from progress import github_group, github_notice, github_warning, ProgressBar
    HAS_PROGRESS = True
except ImportError:
    HAS_PROGRESS = False
    # Fallback no-op context manager
    class github_group:
        def __init__(self, name): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
    def github_notice(msg): print(f"Notice: {msg}")
    def github_warning(msg): print(f"Warning: {msg}")


def load_existing_data(filepath: Path) -> dict:
    """Load existing papers data."""
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'papers': [], 'last_updated': None}


def save_data(filepath: Path, data: dict):
    """Save papers data to JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved data to {filepath}")


def remove_old_papers(papers: list, days: int = 7) -> list:
    """Remove papers older than specified days."""
    cutoff = datetime.now() - timedelta(days=days)
    filtered = []

    for paper in papers:
        try:
            paper_date = datetime.strptime(paper['published'], '%Y-%m-%d')
            if paper_date >= cutoff:
                filtered.append(paper)
        except (ValueError, KeyError):
            filtered.append(paper)

    removed = len(papers) - len(filtered)
    if removed > 0:
        print(f"✓ Removed {removed} papers older than {days} days")

    return filtered


def merge_papers(existing: list, new: list) -> list:
    """Merge new papers with existing, avoiding duplicates and updating with new data."""
    existing_dict = {p['id']: p for p in existing}

    new_count = 0
    updated_count = 0
    for paper in new:
        if paper['id'] not in existing_dict:
            existing_dict[paper['id']] = paper
            new_count += 1
        else:
            if paper.get('summary_status') == 'success':
                existing_dict[paper['id']] = paper
                updated_count += 1

    print(f"✓ Added {new_count} new papers, updated {updated_count} papers")
    return list(existing_dict.values())


def retry_failed_summaries(failed_papers: list, summarizer: ModelScopeSummarizer) -> tuple:
    """Retry summarization for failed papers."""
    if not failed_papers:
        return [], []

    print(f"\nRetrying {len(failed_papers)} previously failed papers...")
    return summarizer.batch_summarize(failed_papers)


def main():
    """Main execution function."""
    print("=" * 70)
    print("📚 Paper Aggregator - Starting")
    print("=" * 70)

    # Configuration
    DAYS_BACK = 7
    DATA_DIR = Path(__file__).parent.parent / 'data'
    PAPERS_FILE = DATA_DIR / 'papers.json'
    FAILED_FILE = DATA_DIR / 'failed.json'

    # Get API key from environment
    api_key = os.getenv('MODELSCOPE_API_KEY') or os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        print("::error::API key not set. Please set DASHSCOPE_API_KEY in GitHub Secrets")
        print("Get your API key from: https://dashscope.console.aliyun.com/")
        sys.exit(1)

    # Initialize components
    with github_group("🔧 Initializing components"):
        print("Creating fetchers and filter...")
        arxiv_fetcher = ArxivFetcher(days_back=DAYS_BACK)
        iacr_fetcher = IACRFetcher(days_back=DAYS_BACK)
        keyword_filter = KeywordFilter()
        summarizer = ModelScopeSummarizer(api_key=api_key)
        print("✓ All components initialized")

    # Load existing data
    with github_group("💾 Loading existing data"):
        existing_data = load_existing_data(PAPERS_FILE)
        existing_failed = load_existing_data(FAILED_FILE)
        print(f"✓ Loaded {len(existing_data.get('papers', []))} existing papers")
        print(f"✓ Loaded {len(existing_failed.get('papers', []))} failed papers")

    # Retry previously failed papers
    retry_successful = []
    if existing_failed.get('papers'):
        with github_group("🔄 Retrying failed summaries"):
            retry_successful, retry_failed = retry_failed_summaries(
                existing_failed['papers'], 
                summarizer
            )
            if retry_successful:
                github_notice(f"Successfully summarized {len(retry_successful)} previously failed papers")

    # Fetch papers from sources
    with github_group("📥 Fetching papers from sources"):
        print("Fetching from arXiv...")
        arxiv_papers = arxiv_fetcher.fetch_papers()
        
        print("\nFetching from IACR...")
        iacr_papers = iacr_fetcher.fetch_papers()
        
        all_fetched = arxiv_papers + iacr_papers
        print(f"\n✓ Total fetched: {len(all_fetched)} papers")
        print(f"  - arXiv: {len(arxiv_papers)} papers")
        print(f"  - IACR: {len(iacr_papers)} papers")

    # Filter by keywords
    with github_group("🔍 Filtering by keywords"):
        filtered_papers = keyword_filter.filter_papers(all_fetched)
        if filtered_papers:
            github_notice(f"Matched {len(filtered_papers)} papers with keywords")
        else:
            github_warning("No papers matched keyword filters")

    # Summarize papers
    with github_group("🤖 Generating AI summaries"):
        if filtered_papers:
            successful, failed = summarizer.batch_summarize(filtered_papers)
        else:
            successful, failed = [], []

    # Combine with retry results
    all_successful = successful + retry_successful
    
    if not all_successful:
        print("\n⚠️  No new papers to add")
        existing_data['last_updated'] = datetime.now().isoformat()
        save_data(PAPERS_FILE, existing_data)
        return

    # Merge with existing papers
    with github_group("📦 Merging with existing data"):
        all_papers = merge_papers(existing_data.get('papers', []), all_successful)
        all_papers = remove_old_papers(all_papers, days=DAYS_BACK)
        all_papers.sort(key=lambda p: p.get('published', '0000-00-00'), reverse=True)

    # Save data
    with github_group("💾 Saving data"):
        papers_data = {
            'papers': all_papers,
            'last_updated': datetime.now().isoformat(),
            'total_count': len(all_papers)
        }
        save_data(PAPERS_FILE, papers_data)

        if failed:
            failed_data = {
                'papers': failed,
                'last_updated': datetime.now().isoformat(),
                'count': len(failed)
            }
            save_data(FAILED_FILE, failed_data)
        elif FAILED_FILE.exists():
            FAILED_FILE.unlink()
            print("✓ Cleared failed papers file (all succeeded)")

    # Summary
    print("\n" + "=" * 70)
    print("✅ Paper Aggregator - Complete")
    print("=" * 70)
    print(f"📊 Statistics:")
    print(f"  Total papers in database: {len(all_papers)}")
    print(f"  New summaries: {len(successful)}")
    print(f"  Retry summaries: {len(retry_successful)}")
    print(f"  Failed summaries: {len(failed)}")
    print(f"  Last updated: {papers_data['last_updated']}")
    print("=" * 70)
    
    github_notice(f"Successfully updated {len(all_papers)} papers")


if __name__ == '__main__':
    main()
