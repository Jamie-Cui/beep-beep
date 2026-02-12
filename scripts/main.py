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
    print(f"Saved data to {filepath}")


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
            # Keep papers with invalid dates
            filtered.append(paper)

    removed = len(papers) - len(filtered)
    if removed > 0:
        print(f"Removed {removed} papers older than {days} days")

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
            # Update if the new version has better data (e.g., successful summary)
            if paper.get('summary_status') == 'success':
                existing_dict[paper['id']] = paper
                updated_count += 1

    print(f"Added {new_count} new papers, updated {updated_count} papers")
    return list(existing_dict.values())


def retry_failed_summaries(failed_papers: list, summarizer: ModelScopeSummarizer) -> tuple:
    """Retry summarization for failed papers."""
    if not failed_papers:
        return [], []

    print(f"\nRetrying summarization for {len(failed_papers)} failed papers...")
    return summarizer.batch_summarize(failed_papers)


def main():
    """Main execution function."""
    print("=" * 60)
    print("Paper Aggregator - Starting")
    print("=" * 60)

    # Configuration
    DAYS_BACK = 7
    DATA_DIR = Path(__file__).parent.parent / 'data'
    PAPERS_FILE = DATA_DIR / 'papers.json'
    FAILED_FILE = DATA_DIR / 'failed.json'

    # Get API key from environment
    api_key = os.getenv('MODELSCOPE_API_KEY')
    if not api_key:
        print("ERROR: MODELSCOPE_API_KEY environment variable not set")
        sys.exit(1)

    # Initialize components
    print("\n1. Initializing components...")
    arxiv_fetcher = ArxivFetcher(days_back=DAYS_BACK)
    iacr_fetcher = IACRFetcher(days_back=DAYS_BACK)
    keyword_filter = KeywordFilter(require_both_categories=True, min_keyword_score=2)
    summarizer = ModelScopeSummarizer(api_key=api_key)

    # Load existing data
    print("\n2. Loading existing data...")
    existing_data = load_existing_data(PAPERS_FILE)
    existing_failed = load_existing_data(FAILED_FILE)

    # Retry previously failed papers
    retry_successful = []
    if existing_failed.get('papers'):
        print("\n3. Retrying previously failed summaries...")
        retry_successful, retry_failed = retry_failed_summaries(
            existing_failed['papers'],
            summarizer
        )
        if retry_successful:
            print(f"Successfully summarized {len(retry_successful)} previously failed papers")
        if retry_failed:
            print(f"{len(retry_failed)} papers still failed after retry")

    # Fetch papers from sources
    print("\n4. Fetching papers from sources...")
    arxiv_papers = arxiv_fetcher.fetch_papers()
    iacr_papers = iacr_fetcher.fetch_papers()

    all_fetched = arxiv_papers + iacr_papers
    print(f"Total fetched: {len(all_fetched)} papers")

    # Filter by keywords
    print("\n5. Filtering papers by keywords...")
    filtered_papers = keyword_filter.filter_papers(all_fetched)

    # Summarize newly fetched papers
    print("\n6. Generating summaries for new papers...")
    successful, failed = summarizer.batch_summarize(filtered_papers) if filtered_papers else ([], [])

    # Combine with retry results
    all_successful = successful + retry_successful

    if not all_successful:
        print("No new papers to add")
        # Still update the timestamp
        existing_data['last_updated'] = datetime.now().isoformat()
        save_data(PAPERS_FILE, existing_data)
        return

    # Merge with existing papers
    print("\n7. Merging with existing data...")
    all_papers = merge_papers(existing_data.get('papers', []), all_successful)

    # Remove old papers
    all_papers = remove_old_papers(all_papers, days=DAYS_BACK)

    # Sort by date (newest first)
    all_papers.sort(key=lambda p: p.get('published', '0000-00-00'), reverse=True)

    # Save data
    print("\n8. Saving data...")
    papers_data = {
        'papers': all_papers,
        'last_updated': datetime.now().isoformat(),
        'total_count': len(all_papers)
    }
    save_data(PAPERS_FILE, papers_data)

    # Save failed papers for retry
    if failed:
        failed_data = {
            'papers': failed,
            'last_updated': datetime.now().isoformat(),
            'count': len(failed)
        }
        save_data(FAILED_FILE, failed_data)
    elif FAILED_FILE.exists():
        # Clear failed file if all succeeded
        FAILED_FILE.unlink()
        print("All summaries succeeded, cleared failed papers file")

    # Summary
    print("\n" + "=" * 60)
    print("Paper Aggregator - Complete")
    print("=" * 60)
    print(f"Total papers in database: {len(all_papers)}")
    print(f"New summaries: {len(successful)}")
    print(f"Retry summaries: {len(retry_successful)}")
    print(f"Failed summaries: {len(failed)}")
    print(f"Last updated: {papers_data['last_updated']}")
    print("=" * 60)


if __name__ == '__main__':
    main()
