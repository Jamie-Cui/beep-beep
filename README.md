# Paper Pulse

Automatically fetches and summarizes research papers from arXiv and IACR ePrint based on customizable keyword filters.

## Features

- 🔄 Daily automatic updates via GitHub Actions
- 📚 Fetches papers from arXiv (customizable categories) and IACR ePrint
- 🤖 AI-powered bilingual summaries (Chinese + English) using DashScope API
- 🗂️ Configurable retention period (default: 7 days)
- 🔍 Flexible keyword filtering (OR between lines, AND within lines)
- 🌐 Bilingual UI with per-card language toggle (中/EN)
- 📋 BibTeX export for citations
- 🎨 Minimal, clean card-based interface
- ✨ Markdown support in summaries

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up GitHub Secrets:
   - `DASHSCOPE_API_KEY` (or `MODELSCOPE_API_KEY`): Your DashScope/ModelScope API key

4. Enable GitHub Actions in your repository

5. Enable GitHub Pages:
   - Go to Settings → Pages
   - Source: Deploy from a branch
   - Branch: `master` (or `main`), folder: `/ (root)`

## Keyword Filtering

The system uses `keywords.txt` to filter papers. Edit this file to customize which papers are included:

- **Each line = OR logic**: Match any line
- **Words on same line = AND logic**: Must match all words
- **Comments**: Lines starting with `#`

Example:
```
transformer            # Matches papers with "transformer"
neural backdoor        # Matches papers with BOTH "neural" AND "backdoor"
federated learning     # Matches papers with "federated learning"
zero knowledge         # Matches papers with "zero knowledge"
```

## Configuration

All settings are managed in `config.toml`:

- **Retention period**: `days_back` (default: 7 days)
- **arXiv categories**: `fetchers.arxiv.categories` (default: cs.CR, cs.AI, cs.LG, cs.CL)
- **AI model**: `summarizer.model` (options: qwen-turbo, qwen-plus, qwen-max)
- **Summary length**: `summarizer.max_tokens` (default: 1500 for bilingual)
- **Rate limits**: `delay` and `rate_limit_delay`

See `CONFIG_GUIDE.md` for detailed configuration options.

## Usage

### Automatic Updates
Papers are automatically fetched daily at 00:00 UTC via GitHub Actions.

### Manual Updates
1. Go to Actions tab in GitHub
2. Select "Fetch Papers" workflow
3. Click "Run workflow"

### Local Testing
```bash
export DASHSCOPE_API_KEY="your-api-key"
python scripts/main.py
```

## Project Structure

```
paper-pulse/
├── .github/workflows/
│   └── fetch-papers.yml      # GitHub Actions workflow
├── scripts/
│   ├── fetchers/
│   │   ├── arxiv.py          # arXiv API fetcher
│   │   └── iacr.py           # IACR API fetcher
│   ├── filter.py             # Keyword filtering
│   ├── summarizer.py         # DashScope AI summarization
│   └── main.py               # Main orchestrator
├── data/
│   ├── papers.json           # Current papers
│   └── failed.json           # Papers with failed summarization
├── config.toml               # Configuration file
├── keywords.txt              # Keyword filter rules
├── index.html                # Main page
├── styles.css                # Styles
├── app.js                    # Frontend logic
└── requirements.txt          # Python dependencies
```

## License

MIT
