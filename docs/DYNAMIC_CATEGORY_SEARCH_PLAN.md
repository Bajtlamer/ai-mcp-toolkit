# Dynamic Category Search Implementation Plan

## Overview
Replace hardcoded vendor patterns with flexible, database-driven category system supporting vendors, people, prices, and custom categories.

## Architecture

### 1. Database Model ✅
- **SearchCategory** document in MongoDB
- Fields: company_id, category_type, entities, ignored_words, trigger_keywords, max_non_category_words, match_score
- Categories: vendor, people, price, custom

### 2. Search Service Updates (In Progress)
Need to update these methods to be async and use categories:

#### `search()` method
- Already async ✅
- Need to pass company_id to `_analyze_query()`
- Need to use detected categories in search

#### `_analyze_query()` method  
- Currently sync, needs to be async
- Should call `_detect_categories()` for dynamic detection
- Keep existing money/ID/date detection
- Add category detection results

#### `_keyword_search()` method
- Update vendor matching section (lines 452-483)
- Replace hardcoded vendor logic with category loop
- Support all category types (vendor, people, price)

## Changes Required

### Step 1: Make _analyze_query async
```python
async def _analyze_query(self, query: str, company_id: str) -> Dict[str, Any]:
    # Existing logic for money, IDs, dates
    # ...
    
    # NEW: Detect categories dynamically
    categories = await self._detect_categories(query, company_id)
    analysis['categories'] = categories
    
    # Update has_vendor for backward compatibility
    if 'vendor' in categories:
        analysis['has_vendor'] = True
        analysis['vendors'] = categories['vendor']['matched_entities']
    
    return analysis
```

### Step 2: Update search() to pass company_id
```python
query_analysis = await self._analyze_query(query, company_id)
```

### Step 3: Replace vendor matching in _keyword_search
```python
# Search by categories (vendors, people, prices, etc.)
if query_analysis.get('categories'):
    for category_type, category_info in query_analysis['categories'].items():
        category = category_info['category']
        
        # For vendor/people categories: match by field
        if category_type in ['vendor', 'people']:
            field_name = 'vendor' if category_type == 'vendor' else 'author'  # or email field
            
            for entity in category_info['matched_entities']:
                resources = await Resource.find(
                    Resource.company_id == company_id,
                    getattr(Resource, field_name) == entity
                ).to_list(limit)
                
                for resource in resources:
                    results.append({
                        'id': str(resource.id),
                        'file_name': resource.file_name,
                        'score': category.match_score,
                        'match_type': f'{category_type}_match',
                        'matched_value': entity,
                        # ...
                    })
        
        # For price category: boost results with amounts
        elif category_type == 'price':
            # If query has amounts, find docs with those amounts
            if query_analysis['money_amounts']:
                # Search by amount (existing logic)
                pass
            else:
                # Just keyword "price" without amount - boost results with any amounts
                resources = await Resource.find(
                    Resource.company_id == company_id,
                    Resource.amounts_cents.exists()
                ).to_list(limit)
                # ...
```

### Step 4: Update frontend badge display
Add new match types:
- `vendor_match` → "Vendor Match" (yellow)
- `people_match` → "People Match" (purple) 
- `price_match` → "Price Match" (green)

## API Endpoints Needed

### Search Config Management
```
GET    /search/categories              # List all categories
GET    /search/categories/:type        # Get category details
POST   /search/categories/:type/entities  # Add entity
DELETE /search/categories/:type/entities/:entity  # Remove entity
PUT    /search/categories/:type/ignored-words  # Update ignored words
PUT    /search/categories/:type/trigger-keywords  # Update triggers
```

### Usage Examples
```
POST /search/categories/vendor/entities
Body: {"entity": "netflix"}

POST /search/categories/people/entities  
Body: {"entity": "john.doe@company.com"}

POST /search/categories/people/entities
Body: {"entity": "Jane Smith"}
```

## UI Pages Needed

### Search Configuration Page (`/settings/search`)
- Tabs for each category type (Vendors, People, Prices, Custom)
- Each tab shows:
  - List of entities with delete button
  - Add new entity input
  - Ignored words (chip input)
  - Trigger keywords (chip input)
  - Match score slider
  - Enable/disable toggle

## Testing Plan

### Test Cases
1. **Vendor matching**
   - "google" → vendor_match
   - "google invoice" → vendor_match (invoice ignored)
   - "google tag manager" → exact_phrase (too many non-vendor words)

2. **People matching**
   - "john doe" → people_match (if john doe in entities)
   - "email from jane" → people_match (if jane@* in entities)
   - "contact john about project" → exact_phrase (too many non-people words)

3. **Price matching**
   - "price" → Shows docs with amounts, price_match
   - "how much cost" → price_match (has trigger "how much")
   - "$100 invoice" → exact amount match (existing logic)

4. **Dynamic updates**
   - Add vendor "netflix" via API
   - Search "netflix" → should show vendor_match
   - Remove vendor → should not match as vendor

## Migration Strategy

1. Deploy SearchCategory model
2. On first search per user, create default categories
3. Old searches still work (backward compatible)
4. Gradually roll out UI for managing categories
5. Future: Auto-populate people from document metadata

## Benefits

✅ No more code changes to add vendors  
✅ User-specific vendor/people lists  
✅ Flexible ignored words per category  
✅ Extensible for custom categories  
✅ Future: ML-based entity extraction  
✅ Per-company configuration  

## Timeline

- Phase 1 (Current): Model + core service logic (2-3 hours)
- Phase 2: API endpoints (1 hour)
- Phase 3: UI for management (2-3 hours)
- Phase 4: Testing + refinement (1-2 hours)

Total: ~1 day of work
