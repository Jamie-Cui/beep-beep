# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Security/Crypto + LLM paper aggregator that automatically fetches papers from arXiv and IACR ePrint, filters them by keywords, and generates AI summaries using Alibaba's DashScope API (Qwen). The system runs daily via GitHub Actions and displays results on a static GitHub Pages site.

## Development Commands

### Running the Paper Fetcher

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key (required)
export DASHSCOPE_API_KEY="your-api-key"
# OR
export MODELSCOPE_API_KEY="your-api-key"

# Run the main fetcher script
python scripts/main.py
```

### Local Testing

```bash
# The script will create/update data/papers.json and data/failed.json
# Open index.html in a browser to view the results locally
```

### Manual Workflow Trigger

The GitHub Actions workflow can be triggered manually from the Actions tab or runs automatically daily at 00:00 UTC.

## Architecture

### Data Flow

1. **Fetching** (`scripts/fetchers/`):
   - `arxiv.py`: Fetches from arXiv API (categories: cs.CR, cs.AI, cs.LG, cs.CL) with 3-second delays between requests
   - `iacr.py`: Fetches from IACR ePrint RSS feed with 2-second delays
   - Both respect rate limits and fetch papers from last 7 days by default

2. **Filtering** (`scripts/filter.py`):
   - Uses `keywords.txt` for flexible OR/AND keyword matching
   - **Line-level OR logic**: Match ANY line in keywords.txt
   - **Word-level AND logic**: ALL words on same line must match
   - Adds `keywords` and `keyword_score` fields to matched papers

3. **Summarization** (`scripts/summarizer.py`):
   - Uses DashScope API (Alibaba Cloud's Qwen model)
   - Default: `qwen-plus` model with 500 max tokens
   - 1-second delay between API calls for rate limiting
   - Retries failed papers on subsequent runs
   - Papers with failed summaries fall back to using abstract

4. **Data Management** (`scripts/main.py`):
   - Merges new papers with existing data (deduplicates by ID)
   - Removes papers older than 7 days automatically
   - Maintains two files: `data/papers.json` (successful) and `data/failed.json` (failed summaries)
   - Retries previously failed summaries on each run

5. **Frontend** (`index.html`, `app.js`, `styles.css`):
   - Static site with client-side filtering/search
   - BibTeX export functionality for citations
   - Card-based UI with source badges (arXiv/IACR)

### Key Data Structures

**Paper object** (as stored in `data/papers.json`):
```javascript
{
  "id": "arxiv_2401.12345" | "iacr_2024/123",
  "title": "...",
  "authors": ["Author1", "Author2"],
  "abstract": "...",
  "summary": "AI-generated summary or fallback to abstract",
  "summary_status": "success" | "failed",
  "published": "YYYY-MM-DD",
  "source": "arXiv" | "IACR",
  "url": "https://...",
  "pdf_link": "https://...",
  "keywords": ["keyword1", "keyword2"],
  "keyword_score": 2,
  "categories": ["cs.CR"],
  "published_official": true,
  "arxiv_id": "2401.12345"  // arXiv only
  "iacr_id": "2024/123"      // IACR only
}
```

### Important Implementation Details

**API Key Environment Variables**: The code checks for both `DASHSCOPE_API_KEY` and `MODELSCOPE_API_KEY` (they're the same service, just different naming). Use `DASHSCOPE_API_KEY` as the primary.

**Rate Limiting**:
- arXiv: 3-second delay between category requests (they request 3+ seconds)
- IACR: 2-second delay
- DashScope API: 1-second delay between summarization calls

**Error Handling in arXiv Fetcher**: The `arxiv.py` fetcher includes critical XML validation (scripts/fetchers/arxiv.py:88-97) to handle malformed entries. Always check for None elements before accessing `.text` attributes to prevent crashes.

**Paper ID Format**:
- arXiv papers: `arxiv_{arxiv_id}` (e.g., `arxiv_2401.12345`)
- IACR papers: `iacr_{year}/{number}` (e.g., `iacr_2024/123`)

**Keyword Matching**: Uses word boundaries (`\b`) in regex for precise matching. The filter is case-insensitive and searches both title and abstract.

**GitHub Actions Automation**: Workflow commits changes with git user `github-actions[bot]` and only commits if there are actual data changes (uses `git diff --staged --quiet` check).

## Configuration Files

- `keywords.txt`: Keyword filter configuration (edit to change paper selection criteria)
- `requirements.txt`: Python dependencies (requests, feedparser, python-dateutil)
- `.github/workflows/fetch-papers.yml`: Daily automation workflow
- `SETUP.md`: Deployment instructions
- `SETUP_API.md`: API key setup instructions (Chinese)

## Common Modification Scenarios

**Changing retention period**: Edit `DAYS_BACK = 7` in `scripts/main.py:95`

**Changing arXiv categories**: Edit `CATEGORIES` list in `scripts/fetchers/arxiv.py:9`

**Changing AI model**: Edit `DEFAULT_MODEL` in `scripts/summarizer.py:15` (e.g., to `qwen-turbo` or `qwen-max`)

**Adjusting rate limits**: Modify delay parameters in fetcher constructors and summarizer

**Customizing summary prompt**: Edit `_create_prompt()` method in `scripts/summarizer.py:48`

## GitHub Pages Deployment

The site deploys from the root directory (`/`) on the master branch. The `index.html`, `app.js`, `styles.css`, and `data/` directory must be in the root for proper deployment.
