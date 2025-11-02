# Search Suggestions User Guide

## What are Search Suggestions?

Search Suggestions is an intelligent autocomplete feature that helps you find documents faster by suggesting relevant search terms as you type. The system learns from your uploaded documents and suggests:

- **File names** - Names of documents you've uploaded
- **Vendors** - Companies and organizations mentioned in your documents
- **Entities** - People, organizations, and important terms
- **Keywords** - Common identifiers like invoice numbers, emails
- **Terms** - Frequently used words from your document content

## How to Use

### Basic Usage

1. **Start typing** in the search box (minimum 2 characters)
2. **Wait 300ms** - Suggestions appear automatically
3. **Click a suggestion** or use keyboard to select
4. **Press Enter** to search

### Keyboard Navigation

| Key | Action |
|-----|--------|
| `↑` (Up Arrow) | Move to previous suggestion |
| `↓` (Down Arrow) | Move to next suggestion |
| `Enter` | Select highlighted suggestion (or search if no suggestion selected) |
| `Esc` | Close suggestions dropdown |

### Example

```
1. Type: "goo"
   → Suggestions appear:
      📄 google cloud invoice.pdf (file)
      🏢 google (vendor)
      🔍 google tag manager (term)

2. Press ↓ to highlight "google"
3. Press Enter to select
4. Press Enter again to search
```

## Suggestion Types

Suggestions are color-coded by type:

| Icon | Type | Color | Description | Example |
|------|------|-------|-------------|---------|
| 📄 | File | Blue | Document file names | `invoice-2024.pdf` |
| 🏢 | Vendor | Blue | Company/vendor names | `Google`, `Microsoft` |
| # | Entity | Green | Extracted entities | `John Doe`, `ACME Corp` |
| 📝 | Keyword | Purple | Document keywords | `contract`, `agreement` |
| 🔍 | Term | Gray | Common content terms | `payment`, `delivery` |

## Tips for Best Results

### 1. Be Specific Early

❌ **Don't**: Type `a` or `b` (too broad)  
✅ **Do**: Type `inv` for invoices, `goo` for Google documents

### 2. Use File Names

File names appear first in suggestions because they're often the most specific way to find a document.

```
Type: "5103"
Suggestion: 📄 5103411658.pdf
```

### 3. Use Vendor Names

If you remember the company/vendor, type their name:

```
Type: "mic"
Suggestions:
  🏢 microsoft
  📄 microsoft azure bill.pdf
```

### 4. Use Partial Words

The system matches from the beginning of words:

```
Type: "tag"
Suggestions:
  🔍 tag manager
  📄 google tag manager.html
```

## How Suggestions are Generated

### Automatic Indexing

When you upload a document, the system automatically:

1. **Extracts terms** from the document
   - File name
   - Text content
   - Metadata (companies, IDs, keywords)

2. **Normalizes text**
   - Removes diacritics (ä → a, č → c)
   - Converts to lowercase
   - Removes extra whitespace

3. **Indexes in Redis**
   - Stores terms for fast retrieval
   - Tracks frequency (more common = higher score)
   - Isolates by user/company (you only see your own data)

### Scoring

Suggestions are ranked by relevance:

```
Score = Type Priority × Frequency

Examples:
- File "google.pdf" (seen 5 times): 1.0 × 5 = 5.0
- Vendor "google" (seen 4 times): 0.9 × 4 = 3.6
- Term "google" (seen 5 times): 0.5 × 5 = 2.5
```

## Privacy & Security

### Multi-Tenant Isolation

✅ **Your data is private**  
- You only see suggestions from your own documents
- No data leakage between users or companies
- Suggestions are company-specific

### No Sensitive Data

✅ **Safe by design**  
- Suggestions don't include passwords or secrets
- PII is not stored in suggestions
- Only metadata and common terms are indexed

## Troubleshooting

### No Suggestions Appearing

**Possible causes:**
1. Query is less than 2 characters → Type more
2. No matching documents → Try different terms
3. Redis is unavailable → Contact administrator
4. Documents not yet indexed → Wait a moment after upload

### Wrong Suggestions

**Possible causes:**
1. Old data → Re-upload documents
2. Multiple companies → Check you're logged into correct account
3. Cached data → Hard refresh browser (Ctrl+Shift+R)

### Suggestions Not Updating

**Solution:**  
1. Wait 5-10 seconds after uploading a file
2. Type a new character to trigger refresh
3. If still not working, contact administrator

## FAQ

### Q: How long does it take for new documents to appear in suggestions?

**A:** Immediately. When you upload a document, it's indexed within seconds and suggestions are available right away.

### Q: Can I search without using suggestions?

**A:** Yes! Suggestions are optional. You can type any query and press Enter to search directly.

### Q: Do suggestions work offline?

**A:** No. Suggestions require an active connection to the backend service (Redis).

### Q: Can I disable suggestions?

**A:** Currently no. However, you can simply ignore them and search normally. We're considering adding a setting in future versions.

### Q: How many suggestions can I see at once?

**A:** Up to 10 suggestions per query. The most relevant ones are shown first.

### Q: Does it work with non-English text?

**A:** Yes! The system supports diacritic-insensitive search, so text with accents (á, ü, ř, etc.) works perfectly. Type without diacritics to find documents with them.

### Q: Can I suggest improvements?

**A:** Absolutely! Please contact your system administrator with feedback and suggestions.

## Related Features

### Exact Phrase Matching

When you search with suggestions or manually, the system prioritizes exact phrase matches:

- **Exact phrase** → 100% score
- **Partial words** → 15-60% score based on word overlap

Example:
- Search: `"End Google Tag Manager"`
- File with entire phrase → 100%
- File with only "google" → 15%

### Diacritic-Insensitive Search

Search works regardless of diacritics:

```
Type: "jak" → Finds "Jak se formuje datová budoucnost"
Type: "formuje" → Finds "Jak se formuje datová budoucnost"
Type: "datova" → Finds "datová" (with accent)
```

---

**Need Help?**

Contact your system administrator or check the [API Documentation](./API_SEARCH_SUGGESTIONS.md) for technical details.

**Last Updated**: 2025-01-02
