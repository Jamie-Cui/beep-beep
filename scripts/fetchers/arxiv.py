import requests
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import xml.etree.ElementTree as ET


class ArxivFetcher:
    """Fetches papers from arXiv API."""

    BASE_URL = "http://export.arxiv.org/api/query"
    CATEGORIES = ["cs.CR", "cs.AI", "cs.LG", "cs.CL"]  # Cryptography, AI, ML, Computation and Language
    BATCH_SIZE = 100
    MAX_RESULTS = 500

    def __init__(self, days_back: int = 7, delay: float = 3.0):
        """
        Initialize arXiv fetcher.

        Args:
            days_back: Number of days to look back for papers
            delay: Delay between requests to respect rate limits (arXiv asks for 3 seconds)
        """
        self.days_back = days_back
        self.delay = delay

    def fetch_papers(self) -> List[Dict]:
        """
        Fetch recent papers from arXiv.

        Returns:
            List of paper dictionaries with metadata
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_back)
        all_papers = []

        for category in self.CATEGORIES:
            print(f"Fetching from arXiv category: {category}")
            papers = self._fetch_category(category, cutoff_date)
            all_papers.extend(papers)
            time.sleep(self.delay)

        # Remove duplicates (papers can appear in multiple categories)
        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            if paper['id'] not in seen_ids:
                seen_ids.add(paper['id'])
                unique_papers.append(paper)

        print(f"Fetched {len(unique_papers)} unique papers from arXiv")
        return unique_papers

    def _fetch_category(self, category: str, cutoff_date: datetime) -> List[Dict]:
        """
        Fetch papers from a specific arXiv category.

        Args:
            category: arXiv category (e.g., 'cs.CR')
            cutoff_date: Only fetch papers after this date

        Returns:
            List of paper dictionaries
        """
        papers = []
        start = 0

        while True:
            params = {
                'search_query': f'cat:{category}',
                'start': start,
                'max_results': self.BATCH_SIZE,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }

            try:
                response = requests.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Error fetching from arXiv category {category}: {e}")
                break

            # Parse XML response
            root = ET.fromstring(response.content)
            namespace = {'atom': 'http://www.w3.org/2005/Atom',
                        'arxiv': 'http://arxiv.org/schemas/atom'}

            entries = root.findall('atom:entry', namespace)

            if not entries:
                break

            for entry in entries:
                # Extract required fields with null checks
                published_elem = entry.find('atom:published', namespace)
                id_elem = entry.find('atom:id', namespace)
                title_elem = entry.find('atom:title', namespace)
                abstract_elem = entry.find('atom:summary', namespace)

                # Skip malformed entries
                if not all([published_elem, id_elem, title_elem, abstract_elem]):
                    print(f"Skipping malformed entry (missing required fields)")
                    continue

                try:
                    published = published_elem.text
                    published_date = datetime.fromisoformat(published.replace('Z', '+00:00'))

                    # Stop if we've gone past the cutoff date
                    if published_date < cutoff_date:
                        return papers

                    # Extract paper metadata
                    paper_id = id_elem.text.split('/abs/')[-1]
                    title = title_elem.text.strip().replace('\n', ' ')
                    abstract = abstract_elem.text.strip().replace('\n', ' ')

                    authors = []
                    for author in entry.findall('atom:author', namespace):
                        name_elem = author.find('atom:name', namespace)
                        if name_elem is not None and name_elem.text:
                            authors.append(name_elem.text)

                    pdf_link = None
                    for link in entry.findall('atom:link', namespace):
                        if link.get('title') == 'pdf':
                            pdf_link = link.get('href')
                            break

                    # Get categories
                    categories = []
                    primary_category = entry.find('arxiv:primary_category', namespace)
                    if primary_category is not None:
                        term = primary_category.get('term')
                        if term:
                            categories.append(term)

                    for cat in entry.findall('atom:category', namespace):
                        term = cat.get('term')
                        if term and term not in categories:
                            categories.append(term)

                    papers.append({
                        'id': f'arxiv_{paper_id}',
                        'arxiv_id': paper_id,
                        'title': title,
                        'authors': authors,
                        'abstract': abstract,
                        'published': published_date.strftime('%Y-%m-%d'),
                        'source': 'arXiv',
                        'pdf_link': pdf_link,
                        'url': f'https://arxiv.org/abs/{paper_id}',
                        'categories': categories,
                        'published_official': True
                    })
                except (AttributeError, ValueError) as e:
                    print(f"Error parsing entry: {e}")
                    continue

            start += self.BATCH_SIZE

            # Limit to avoid excessive requests
            if start >= self.MAX_RESULTS:
                break

        return papers
