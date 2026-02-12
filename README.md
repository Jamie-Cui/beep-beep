# Security/Crypto + LLM Paper Aggregator

Automatically fetches and summarizes papers from arXiv and IACR related to security, cryptography, and large language models.

## Features

- 🔄 Daily automatic updates via GitHub Actions
- 📚 Fetches papers from arXiv (cs.CR, cs.AI, cs.LG) and IACR ePrint
- 🤖 AI-powered summaries using ModelScope API
- 🗂️ Keeps last 7 days of papers
- 🔍 Smart keyword filtering for security/crypto + LLM topics
- 📋 BibTeX export for citations
- 🎨 Minimal, clean card-based UI

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up GitHub Secrets:
   - `MODELSCOPE_API_KEY`: Your ModelScope API key

4. Enable GitHub Actions in your repository

5. Enable GitHub Pages:
   - Go to Settings → Pages
   - Source: Deploy from a branch
   - Branch: `master` (or `main`), folder: `/web`

## Usage

### Automatic Updates
Papers are automatically fetched daily at 00:00 UTC via GitHub Actions.

### Manual Updates
1. Go to Actions tab in GitHub
2. Select "Fetch Papers" workflow
3. Click "Run workflow"

## Project Structure

```
beep-beep/
├── .github/workflows/
│   └── fetch-papers.yml      # GitHub Actions workflow
├── scripts/
│   ├── fetchers/
│   │   ├── arxiv.py          # arXiv API fetcher
│   │   └── iacr.py           # IACR API fetcher
│   ├── filter.py             # Keyword filtering
│   ├── summarizer.py         # ModelScope AI summarization
│   └── main.py               # Main orchestrator
├── data/
│   ├── papers.json           # Current papers
│   └── failed.json           # Papers with failed summarization
├── web/
│   ├── index.html            # Main page
│   ├── styles.css            # Styles
│   └── app.js                # Frontend logic
└── requirements.txt          # Python dependencies
```

## License

MIT
