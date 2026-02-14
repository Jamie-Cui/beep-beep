# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Paper Pulse** is a keyword-based research paper aggregator that automatically fetches papers from arXiv and IACR ePrint, filters them by customizable keywords, and generates bilingual AI summaries using Alibaba's DashScope API (Qwen). The system runs daily via GitHub Actions and displays results on a static GitHub Pages site.

**Key Characteristics**:
- Domain-agnostic: Uses keyword filtering to match papers (not limited to specific fields)
- Bilingual: Generates both Chinese and English summaries
- Configurable: All major settings managed via `config.toml`

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
   - `arxiv.py`: Fetches from arXiv API (configurable categories, default: cs.CR, cs.AI, cs.LG, cs.CL) with 3-second delays between requests
   - `iacr.py`: Fetches from IACR ePrint RSS feed with 2-second delays
   - Both respect rate limits and fetch papers from configurable time period (default: 7 days)

2. **Filtering** (`scripts/filter.py`):
   - Uses `keywords.txt` for flexible OR/AND keyword matching
   - **Line-level OR logic**: Match ANY line in keywords.txt
   - **Word-level AND logic**: ALL words on same line must match
   - Adds `keywords` and `keyword_score` fields to matched papers

3. **Summarization** (`scripts/summarizer.py`):
   - Uses DashScope API (Alibaba Cloud's Qwen model)
   - Default: `qwen-plus` model with 1500 max tokens
   - Generates **bilingual summaries** (Chinese and English) in a single API call
   - Chinese summary (~60-70% of output) + English summary (~30-40% of output)
   - Uses structured prompt with `[中文摘要]` and `[English Summary]` markers for parsing
   - Supports Markdown formatting in summaries
   - 1-second delay between API calls for rate limiting
   - Retries failed papers with exponential backoff (max 3 retries, 5s delay)
   - Papers with failed summaries fall back to using abstract

4. **Data Management** (`scripts/main.py`):
   - Merges new papers with existing data (deduplicates by ID)
   - Removes papers older than 7 days automatically
   - Maintains two files: `data/papers.json` (successful) and `data/failed.json` (failed summaries)
   - Retries previously failed summaries on each run

5. **Frontend** (`index.html`, `app.js`, `styles.css`):
   - Static site with client-side filtering/search
   - **Bilingual summary toggle** (中/EN buttons) on each paper card
   - Markdown rendering using marked.js library (CDN: https://cdn.jsdelivr.net/npm/marked/marked.min.js)
   - BibTeX export functionality for citations (single paper and bulk export)
   - Card-based UI with source badges (arXiv/IACR)
   - Summary language state managed per-card via `toggleLanguage(index, lang)` function

### Key Data Structures

**Paper object** (as stored in `data/papers.json`):
```javascript
{
  "id": "arxiv_2401.12345" | "iacr_2024/123",
  "title": "...",
  "authors": ["Author1", "Author2"],
  "abstract": "...",
  "summary": "Chinese summary (default, backward compatibility)",
  "summary_zh": "AI-generated Chinese summary (Markdown format)",
  "summary_en": "AI-generated English summary (Markdown format)",
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

- `config.toml`: **Main configuration file** - controls all customizable behavior (prompt, cache duration, API settings, etc.)
- `keywords.txt`: Keyword filter configuration (edit to change paper selection criteria)
- `requirements.txt`: Python dependencies (requests, feedparser, python-dateutil, tomli)
- `.github/workflows/fetch-papers.yml`: Daily automation workflow
- `SETUP.md`: Deployment instructions
- `SETUP_API.md`: API key setup instructions (Chinese)
- `CONFIG_GUIDE.md`: Detailed configuration guide (Chinese)

## Common Modification Scenarios

**All configuration changes should be made in `config.toml` (preferred method):**

**Changing retention period**: Edit `days_back` in `[general]` section of `config.toml`

**Changing arXiv categories**: Edit `categories` list in `[fetchers.arxiv]` section of `config.toml`

**Changing AI model**: Edit `model` in `[summarizer]` section of `config.toml` (e.g., to `qwen-turbo` or `qwen-max`)

**Adjusting rate limits**: Edit `delay` and `rate_limit_delay` in `config.toml`

**Customizing summary prompt**:
- **For bilingual summaries**: Edit `_create_bilingual_prompt()` method in `scripts/summarizer.py` (lines ~92-115)
- **For single-language summaries**: Edit `prompt_template` in `[summarizer]` section of `config.toml` - must include `{title}` and `{abstract}` placeholders
- **IMPORTANT**: Bilingual prompt is hard-coded in Python for better control over format and parsing

See `CONFIG_GUIDE.md` for detailed configuration examples and best practices.

## GitHub Pages Deployment

The site deploys from the root directory (`/`) on the master branch. The `index.html`, `app.js`, `styles.css`, and `data/` directory must be in the root for proper deployment.

## Bilingual Summary Architecture

**Critical Implementation Details**:

1. **Summary Generation** (scripts/summarizer.py:92-115):
   - Single API call generates both Chinese and English summaries
   - Structured prompt uses `[中文摘要]` and `[English Summary]` as section markers
   - Token allocation: ~60-70% Chinese, ~30-40% English (total: 1500 tokens)
   - Supports Markdown formatting (headings, bold, lists)

2. **Summary Parsing** (scripts/summarizer.py:117-138):
   - Regex-based extraction using section markers
   - Fallback parsing if markers are malformed
   - If parsing fails completely, uses full response for both languages

3. **Frontend Language Toggle** (app.js:14-35):
   - `toggleLanguage(index, lang)` function switches between Chinese ('zh') and English ('en')
   - State stored in `data-lang` attribute on summary div
   - Button styling managed via `.active` class
   - Markdown rendering applied via `renderMarkdown()` helper

4. **Backward Compatibility**:
   - `summary` field defaults to `summary_zh` for legacy support
   - If only `summary` exists (old data), both language toggles show same content
   - Language toggle UI only appears when both `summary_zh` and `summary_en` exist

**When modifying bilingual summaries**:
- Do NOT change section markers without updating parser regex in `_parse_bilingual_summary()`
- Token limit (`max_tokens` in config.toml) must accommodate both languages
- Test with real API calls, as model output format can vary
