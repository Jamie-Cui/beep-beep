# Setup Guide

This guide will help you set up and deploy your Security/Crypto + LLM Paper Aggregator on GitHub Pages.

## Prerequisites

- GitHub account
- ModelScope API key (free tier available at https://modelscope.cn)
- Git installed locally

## Step 1: Repository Setup

1. Push this code to your GitHub repository:
   ```bash
   git add .
   git commit -m "Initial commit: Paper aggregator"
   git push origin master
   ```

## Step 2: Configure GitHub Secrets

1. Go to your repository on GitHub
2. Click on **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secret:
   - Name: `MODELSCOPE_API_KEY`
   - Value: Your ModelScope API key

## Step 3: Enable GitHub Actions

1. Go to the **Actions** tab in your repository
2. If prompted, click **I understand my workflows, go ahead and enable them**
3. The workflow should now be enabled

## Step 4: Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Under **Source**, select:
   - Source: **Deploy from a branch**
   - Branch: **master** (or **main** if that's your default branch)
   - Folder: **/web**
3. Click **Save**
4. Wait a few minutes for the site to deploy
5. Your site will be available at: `https://<username>.github.io/<repo-name>/`

## Step 5: First Run

### Option A: Manual Trigger (Recommended for first run)

1. Go to **Actions** tab
2. Click on **Fetch Papers** workflow
3. Click **Run workflow** → **Run workflow**
4. Wait for the workflow to complete (5-10 minutes depending on number of papers)

### Option B: Wait for Automatic Run

The workflow runs automatically every day at 00:00 UTC.

## Step 6: Verify

1. After the workflow completes, check that `data/papers.json` has been created
2. Visit your GitHub Pages URL
3. You should see the papers displayed in card format

## Troubleshooting

### Workflow fails with "MODELSCOPE_API_KEY not set"
- Make sure you've added the secret in Step 2
- The secret name must be exactly `MODELSCOPE_API_KEY`

### No papers showing up
- Check the workflow logs to see if papers were fetched
- Papers must match BOTH security/crypto AND LLM/AI keywords
- Only papers from the last 7 days are kept

### GitHub Pages shows 404
- Make sure you selected `/web` as the folder in Pages settings
- Wait a few minutes after enabling Pages for DNS to propagate
- Check that `web/index.html` exists in your repository

### Rate limiting issues
- The default delays (3s for arXiv, 1s for summarization) should prevent rate limiting
- If you still hit limits, you can increase delays in the code

## Customization

### Change keyword filters

Edit `scripts/filter.py` to add or modify keywords in:
- `SECURITY_CRYPTO_KEYWORDS`
- `LLM_AI_KEYWORDS`

### Change how many days of papers to keep

Edit `scripts/main.py`, line 95:
```python
DAYS_BACK = 7  # Change this number
```

### Change workflow schedule

Edit `.github/workflows/fetch-papers.yml`, line 5:
```yaml
- cron: '0 0 * * *'  # Daily at 00:00 UTC
```

Use [crontab.guru](https://crontab.guru/) to generate different schedules.

## Manual Local Testing

Test the fetcher locally before deploying:

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key
export MODELSCOPE_API_KEY="your-key-here"

# Run the script
python scripts/main.py
```

This will create `data/papers.json` which you can inspect.

## License

MIT
