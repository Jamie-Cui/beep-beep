// Global state
let allPapers = [];
let filteredPapers = [];

// Load papers on page load
document.addEventListener('DOMContentLoaded', () => {
    loadPapers();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    const searchInput = document.getElementById('searchInput');
    const sourceFilter = document.getElementById('sourceFilter');
    const sortBy = document.getElementById('sortBy');
    const exportAllBtn = document.getElementById('exportAllBtn');

    searchInput.addEventListener('input', filterAndDisplay);
    sourceFilter.addEventListener('change', filterAndDisplay);
    sortBy.addEventListener('change', filterAndDisplay);
    exportAllBtn.addEventListener('click', exportAllPapers);
}

// Toggle language for a specific paper card
function toggleLanguage(index, lang) {
    const summaryDiv = document.querySelector(`#paper-summary-${index}`);
    const zhBtn = document.querySelector(`#lang-zh-${index}`);
    const enBtn = document.querySelector(`#lang-en-${index}`);

    if (!summaryDiv || !zhBtn || !enBtn) return;

    const paper = filteredPapers[index];
    if (!paper) return;

    // Get the appropriate summary
    const summaryText = lang === 'zh'
        ? (paper.summary_zh || paper.summary || paper.abstract)
        : (paper.summary_en || paper.summary || paper.abstract);

    // Update content
    summaryDiv.innerHTML = renderMarkdown(summaryText);
    summaryDiv.dataset.lang = lang;

    // Update button states
    if (lang === 'zh') {
        zhBtn.classList.add('active');
        enBtn.classList.remove('active');
    } else {
        zhBtn.classList.remove('active');
        enBtn.classList.add('active');
    }
}

// Load papers from JSON
async function loadPapers() {
    try {
        const response = await fetch('data/papers.json');
        if (!response.ok) {
            throw new Error('Failed to load papers');
        }

        const data = await response.json();
        allPapers = data.papers || [];

        // Update last updated time
        if (data.last_updated) {
            const date = new Date(data.last_updated);
            document.getElementById('lastUpdated').textContent = date.toLocaleString();
        }

        filterAndDisplay();
    } catch (error) {
        console.error('Error loading papers:', error);
        document.getElementById('papersList').innerHTML =
            '<div class="no-results">Failed to load papers. Please try again later.</div>';
    }
}

// Filter and display papers
function filterAndDisplay() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const sourceFilter = document.getElementById('sourceFilter').value;
    const sortBy = document.getElementById('sortBy').value;

    // Filter papers
    filteredPapers = allPapers.filter(paper => {
        // Source filter
        if (sourceFilter !== 'all' && paper.source !== sourceFilter) {
            return false;
        }

        // Search filter
        if (searchTerm) {
            const searchableText = [
                paper.title,
                paper.authors.join(' '),
                paper.summary,
                paper.abstract,
                ...(paper.keywords || [])
            ].join(' ').toLowerCase();

            if (!searchableText.includes(searchTerm)) {
                return false;
            }
        }

        return true;
    });

    // Sort papers
    sortPapers(filteredPapers, sortBy);

    // Display papers
    displayPapers(filteredPapers);
    updateStats(filteredPapers.length, allPapers.length);
}

// Sort papers
function sortPapers(papers, sortBy) {
    switch (sortBy) {
        case 'date-desc':
            papers.sort((a, b) => b.published.localeCompare(a.published));
            break;
        case 'date-asc':
            papers.sort((a, b) => a.published.localeCompare(b.published));
            break;
        case 'title':
            papers.sort((a, b) => a.title.localeCompare(b.title));
            break;
    }
}

// Display papers
function displayPapers(papers) {
    const papersList = document.getElementById('papersList');

    if (papers.length === 0) {
        papersList.innerHTML = '<div class="no-results">No papers found matching your criteria.</div>';
        return;
    }

    papersList.innerHTML = papers.map((paper, index) => createPaperCard(paper, index)).join('');

    // Add event listeners for BibTeX buttons
    papers.forEach((paper, index) => {
        const btn = document.getElementById(`bibtex-${index}`);
        if (btn) {
            btn.addEventListener('click', () => exportBibtex(paper));
        }
    });
}

// Render Markdown to HTML
function renderMarkdown(text) {
    if (!text) return '';

    // Use marked.js to parse Markdown
    if (typeof marked !== 'undefined') {
        return marked.parse(text);
    }

    // Fallback: basic line break conversion
    return escapeHtml(text).replace(/\n/g, '<br>');
}

// Create paper card HTML
function createPaperCard(paper, index) {
    const authors = paper.authors.slice(0, 5).join(', ') +
                   (paper.authors.length > 5 ? ', et al.' : '');

    const sourceBadge = `<span class="source-badge source-${paper.source.toLowerCase()}">${paper.source}</span>`;

    const keywords = (paper.keywords || [])
        .slice(0, 8)
        .map(kw => `<span class="keyword-tag">${kw}</span>`)
        .join('');

    // Default to Chinese summary
    const summaryText = paper.summary_zh || paper.summary || paper.abstract;
    const summaryHtml = renderMarkdown(summaryText);

    // Check if bilingual summaries are available
    const hasBilingual = paper.summary_zh && paper.summary_en;

    return `
        <div class="paper-card">
            <div class="paper-header">
                <h2 class="paper-title">${escapeHtml(paper.title)}</h2>
                <div class="paper-meta">
                    ${sourceBadge}
                    <span>📅 ${paper.published}</span>
                    ${paper.published_official ? '<span>✓ Official Publication</span>' : '<span>📝 Preprint</span>'}
                </div>
            </div>

            <div class="paper-authors">
                <strong>Authors:</strong> ${escapeHtml(authors)}
            </div>

            <div class="summary-container">
                ${hasBilingual ? `
                <div class="lang-toggle-group">
                    <button class="lang-toggle-btn active" id="lang-zh-${index}" onclick="toggleLanguage(${index}, 'zh')">中</button>
                    <button class="lang-toggle-btn" id="lang-en-${index}" onclick="toggleLanguage(${index}, 'en')">EN</button>
                </div>
                ` : ''}
                <div class="paper-summary" id="paper-summary-${index}" data-lang="zh">
                    ${summaryHtml}
                </div>
            </div>

            ${keywords ? `<div class="paper-keywords">${keywords}</div>` : ''}

            <div class="paper-actions">
                <a href="${paper.url}" target="_blank" class="view-link">View Abstract</a>
                ${paper.pdf_link ? `<a href="${paper.pdf_link}" target="_blank" class="pdf-link">Download PDF</a>` : ''}
                <button id="bibtex-${index}" class="bibtex-btn">Export BibTeX</button>
            </div>
        </div>
    `;
}

// Update statistics
function updateStats(filtered, total) {
    const stats = document.getElementById('stats');
    stats.textContent = `Showing ${filtered} of ${total} papers`;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Generate BibTeX entry
function generateBibtex(paper) {
    const year = paper.published.split('-')[0];
    const authors = paper.authors.join(' and ');

    // Generate citation key
    const firstAuthor = paper.authors[0]?.split(' ').pop() || 'Unknown';
    const titleWords = paper.title.split(' ').slice(0, 2).join('');
    const key = `${firstAuthor}${year}${titleWords}`.replace(/[^a-zA-Z0-9]/g, '');

    // Determine entry type
    let entryType = 'article';
    let venue = '';

    if (paper.source === 'arXiv') {
        entryType = 'misc';
        venue = `  eprint = {${paper.arxiv_id}},\n  archivePrefix = {arXiv},`;
    } else if (paper.source === 'IACR') {
        entryType = 'misc';
        venue = `  howpublished = {Cryptology ePrint Archive, Paper ${paper.iacr_id}},\n  note = {\\url{${paper.url}}},`;
    }

    return `@${entryType}{${key},
  author = {${authors}},
  title = {${paper.title}},
  year = {${year}},
${venue}
  url = {${paper.url}}
}`;
}

// Export single paper as BibTeX
function exportBibtex(paper) {
    const bibtex = generateBibtex(paper);
    downloadText(bibtex, `${paper.id}.bib`);
}

// Export all papers as BibTeX
function exportAllPapers() {
    if (filteredPapers.length === 0) {
        alert('No papers to export');
        return;
    }

    const allBibtex = filteredPapers.map(p => generateBibtex(p)).join('\n\n');
    downloadText(allBibtex, 'papers.bib');
}

// Download text as file
function downloadText(text, filename) {
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
