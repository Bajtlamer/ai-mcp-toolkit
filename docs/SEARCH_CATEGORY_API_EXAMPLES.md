# Search Category API Usage Examples

## Overview
The dynamic search category system allows you to configure vendors, people, prices, and custom categories without code changes.

## API Endpoints

### 1. List All Categories
```bash
curl -X GET http://localhost:8000/search/categories \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "vendor": {
    "category_type": "vendor",
    "entities": ["google", "t-mobile", "amazon", "microsoft", ...],
    "ignored_words": ["invoice", "bill", "payment", ...],
    "trigger_keywords": ["vendor", "supplier", "provider"],
    "max_non_category_words": 1,
    "match_score": 0.88,
    "enabled": true
  },
  "people": {
    "category_type": "people",
    "entities": [],
    "ignored_words": ["email", "from", "to", ...],
    ...
  },
  "price": {
    "category_type": "price",
    "entities": [],
    "trigger_keywords": ["price", "cost", "amount", ...],
    ...
  }
}
```

### 2. Get Specific Category
```bash
curl -X GET http://localhost:8000/search/categories/vendor \
  --cookie "session=YOUR_SESSION_COOKIE"
```

### 3. Add Vendor
```bash
curl -X POST http://localhost:8000/search/categories/vendor/entities \
  -H "Content-Type: application/json" \
  -d '{"entity": "netflix"}' \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "message": "Entity 'netflix' added to category 'vendor'",
  "entities": ["google", "t-mobile", ..., "netflix"]
}
```

### 4. Add Person/Email
```bash
# Add email
curl -X POST http://localhost:8000/search/categories/people/entities \
  -H "Content-Type: application/json" \
  -d '{"entity": "john.doe@company.com"}' \
  --cookie "session=YOUR_SESSION_COOKIE"

# Add name
curl -X POST http://localhost:8000/search/categories/people/entities \
  -H "Content-Type": "application/json" \
  -d '{"entity": "jane smith"}' \
  --cookie "session=YOUR_SESSION_COOKIE"
```

### 5. Remove Entity
```bash
curl -X DELETE http://localhost:8000/search/categories/vendor/entities/netflix \
  --cookie "session=YOUR_SESSION_COOKIE"
```

### 6. Update Ignored Words
```bash
curl -X PUT http://localhost:8000/search/categories/vendor/ignored-words \
  -H "Content-Type: application/json" \
  -d '{"ignored_words": ["invoice", "bill", "payment", "contract", "subscription"]}' \
  --cookie "session=YOUR_SESSION_COOKIE"
```

## Testing the Feature

### Step 1: Start the Backend
```bash
python main.py
```

The backend will automatically create default categories on first search.

### Step 2: Add a New Vendor via API
```bash
curl -X POST http://localhost:8000/search/categories/vendor/entities \
  -H "Content-Type: application/json" \
  -d '{"entity": "netflix"}' \
  --cookie "session=$(grep session ~/.config/warp-terminal/cookies.txt | cut -f7)"
```

### Step 3: Search for the New Vendor
```bash
curl -X POST http://localhost:8000/resources/compound-search \
  -H "Content-Type: application/json" \
  -d '{"query": "netflix invoice", "limit": 10}' \
  --cookie "session=YOUR_SESSION"
```

Expected: Returns results with `"match_type": "vendor_match"` and score `0.88` (or exact phrase if the text exists).

### Step 4: Test People Category
```bash
# Add a person
curl -X POST http://localhost:8000/search/categories/people/entities \
  -H "Content-Type: application/json" \
  -d '{"entity": "john doe"}' \
  --cookie "session=YOUR_SESSION"

# Search for documents related to that person
curl -X POST http://localhost:8000/resources/compound-search \
  -H "Content-Type: application/json" \
  -d '{"query": "email from john", "limit": 10}' \
  --cookie "session=YOUR_SESSION"
```

Expected: Returns documents containing "john doe" in entities field with `"match_type": "people_match"`.

### Step 5: Test Price Category
```bash
# Search with price keyword (no specific amount)
curl -X POST http://localhost:8000/resources/compound-search \
  -H "Content-Type: application/json" \
  -d '{"query": "price", "limit": 10}' \
  --cookie "session=YOUR_SESSION"
```

Expected: Returns documents that have `amounts_cents` field populated with `"match_type": "price_match"`.

## Frontend Integration

The search results will automatically display the correct badges:

- 🏭 **Vendor Match** (yellow badge)
- 👤 **People Match** (red badge)  
- 💰 **Price Match** (green badge)
- ✨ **Exact Phrase** (green badge)

## Match Type Priority

When the same document matches multiple ways, the system prefers:

1. **Exact Phrase** (100%) - Text found verbatim in content
2. **Exact Keyword** (100%) - Matches document keyword tags
3. **Price Match** (90%) - Triggered by price keywords + has amounts
4. **Vendor Match** (88%) - Document vendor field matches
5. **People Match** (85%) - Document entities field matches
6. **Partial Match** (50-60%) - Some words found

## Common Use Cases

### Use Case 1: Add All Your Vendors
```bash
for vendor in "spotify" "notion" "figma" "linear"; do
  curl -X POST http://localhost:8000/search/categories/vendor/entities \
    -H "Content-Type: application/json" \
    -d "{\"entity\": \"$vendor\"}" \
    --cookie "session=YOUR_SESSION"
done
```

### Use Case 2: Add Team Members
```bash
# Add team emails
for email in "alice@company.com" "bob@company.com" "charlie@company.com"; do
  curl -X POST http://localhost:8000/search/categories/people/entities \
    -H "Content-Type: application/json" \
    -d "{\"entity\": \"$email\"}" \
    --cookie "session=YOUR_SESSION"
done
```

### Use Case 3: Customize Ignored Words for Your Domain
```bash
# If you work in legal, you might want to ignore "contract" less
curl -X PUT http://localhost:8000/search/categories/vendor/ignored-words \
  -H "Content-Type: application/json" \
  -d '{"ignored_words": ["invoice", "bill", "payment"]}' \
  --cookie "session=YOUR_SESSION"
```

## Troubleshooting

### Categories Not Created
- Categories are created automatically on first search
- Or manually trigger: `GET /search/categories` to initialize

### Entity Not Matching
- Check entity is added: `GET /search/categories/vendor`
- Ensure entity name matches exactly (case-insensitive)
- Check document has correct field populated (vendor field for vendors, entities for people)

### Wrong Badge Displayed
- Check browser console for response data
- Verify `match_type` field in API response
- Clear browser cache if needed

## Next Steps

- UI for managing categories (coming soon)
- Auto-populate people from document metadata
- ML-based entity extraction
- Custom category types
