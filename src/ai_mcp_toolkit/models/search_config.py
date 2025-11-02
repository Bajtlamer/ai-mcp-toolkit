"""Search configuration model for dynamic vendor, people, and category management."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from beanie import Document
from pydantic import Field


class SearchCategory(Document):
    """
    Search category configuration (vendors, people, prices, etc.).
    
    Each category defines entities to match and context words to ignore
    when determining if a query is primarily about that category.
    """
    
    company_id: str = Field(..., description="Company/user ID for multi-tenancy")
    category_type: str = Field(..., description="Category type: vendor, people, price, custom")
    
    # Entities to match (e.g., vendor names, people names/emails)
    entities: List[str] = Field(default_factory=list, description="List of entities in this category")
    
    # Context words to ignore when counting non-category words
    ignored_words: List[str] = Field(
        default_factory=list,
        description="Words to ignore when determining if query is about this category"
    )
    
    # Special keywords that trigger this category
    trigger_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that explicitly trigger this category search"
    )
    
    # Matching configuration
    max_non_category_words: int = Field(
        default=1,
        description="Maximum non-category words allowed to trigger category match"
    )
    
    match_score: float = Field(
        default=0.88,
        description="Score assigned to category matches (0.0-1.0)"
    )
    
    enabled: bool = Field(default=True, description="Whether this category is active")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    class Settings:
        name = "search_categories"
        indexes = [
            "company_id",
            "category_type",
            [("company_id", 1), ("category_type", 1)],
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "user123",
                "category_type": "vendor",
                "entities": ["google", "t-mobile", "amazon"],
                "ignored_words": ["invoice", "bill", "payment", "contract"],
                "trigger_keywords": ["vendor", "supplier", "from"],
                "max_non_category_words": 1,
                "match_score": 0.88,
                "enabled": True
            }
        }


class SearchConfigService:
    """Service for managing search configurations."""
    
    @staticmethod
    async def get_or_create_defaults(company_id: str) -> Dict[str, SearchCategory]:
        """
        Get existing search categories or create defaults for a company.
        
        Args:
            company_id: Company/user ID
            
        Returns:
            Dict mapping category_type to SearchCategory
        """
        # Check if configs exist
        existing = await SearchCategory.find(
            SearchCategory.company_id == company_id
        ).to_list()
        
        if existing:
            return {cat.category_type: cat for cat in existing}
        
        # Create defaults
        defaults = [
            # Vendor category
            SearchCategory(
                company_id=company_id,
                category_type="vendor",
                entities=[
                    "google", "t-mobile", "tmobile", "amazon", "aws", "microsoft",
                    "apple", "adobe", "salesforce", "zoom", "slack", "stripe",
                    "github", "gitlab", "digitalocean", "cloudflare"
                ],
                ignored_words=[
                    "invoice", "invoices", "bill", "bills", "payment", "payments",
                    "contract", "contracts", "subscription", "subscriptions",
                    "from", "by", "provider", "service"
                ],
                trigger_keywords=["vendor", "supplier", "provider", "company"],
                max_non_category_words=1,
                match_score=0.88,
                enabled=True
            ),
            
            # People category
            SearchCategory(
                company_id=company_id,
                category_type="people",
                entities=[],  # Will be populated dynamically from emails/names in docs
                ignored_words=[
                    "email", "emails", "from", "to", "cc", "bcc",
                    "contact", "contacts", "person", "people",
                    "sent", "received", "message", "messages",
                    "by", "author", "sender", "recipient"
                ],
                trigger_keywords=["person", "people", "contact", "email", "who", "sender"],
                max_non_category_words=1,
                match_score=0.85,
                enabled=True
            ),
            
            # Price category
            SearchCategory(
                company_id=company_id,
                category_type="price",
                entities=[],  # No specific entities, works with amounts
                ignored_words=[
                    "total", "sum", "amount", "paid", "cost", "costs",
                    "expense", "expenses", "charge", "charges",
                    "fee", "fees", "value", "worth"
                ],
                trigger_keywords=[
                    "price", "prices", "cost", "costs", "amount", "amounts",
                    "number", "numbers", "how much", "what price"
                ],
                max_non_category_words=2,  # More flexible for price queries
                match_score=0.90,
                enabled=True
            )
        ]
        
        # Insert defaults
        for category in defaults:
            await category.insert()
        
        return {cat.category_type: cat for cat in defaults}
    
    @staticmethod
    async def add_entity(company_id: str, category_type: str, entity: str) -> SearchCategory:
        """
        Add an entity to a category (e.g., add a new vendor).
        
        Args:
            company_id: Company/user ID
            category_type: Category type (vendor, people, etc.)
            entity: Entity to add (normalized to lowercase)
            
        Returns:
            Updated SearchCategory
        """
        category = await SearchCategory.find_one(
            SearchCategory.company_id == company_id,
            SearchCategory.category_type == category_type
        )
        
        if not category:
            # Create category if it doesn't exist
            categories = await SearchConfigService.get_or_create_defaults(company_id)
            category = categories.get(category_type)
            if not category:
                raise ValueError(f"Unknown category type: {category_type}")
        
        entity_lower = entity.lower().strip()
        if entity_lower not in category.entities:
            category.entities.append(entity_lower)
            category.updated_at = datetime.utcnow()
            await category.save()
        
        return category
    
    @staticmethod
    async def remove_entity(company_id: str, category_type: str, entity: str) -> SearchCategory:
        """Remove an entity from a category."""
        category = await SearchCategory.find_one(
            SearchCategory.company_id == company_id,
            SearchCategory.category_type == category_type
        )
        
        if not category:
            raise ValueError(f"Category not found: {category_type}")
        
        entity_lower = entity.lower().strip()
        if entity_lower in category.entities:
            category.entities.remove(entity_lower)
            category.updated_at = datetime.utcnow()
            await category.save()
        
        return category
    
    @staticmethod
    async def get_all_entities(company_id: str, category_type: str) -> List[str]:
        """Get all entities for a category."""
        category = await SearchCategory.find_one(
            SearchCategory.company_id == company_id,
            SearchCategory.category_type == category_type
        )
        
        if not category:
            categories = await SearchConfigService.get_or_create_defaults(company_id)
            category = categories.get(category_type)
        
        return category.entities if category else []
    
    @staticmethod
    async def update_ignored_words(
        company_id: str,
        category_type: str,
        ignored_words: List[str]
    ) -> SearchCategory:
        """Update ignored words for a category."""
        category = await SearchCategory.find_one(
            SearchCategory.company_id == company_id,
            SearchCategory.category_type == category_type
        )
        
        if not category:
            raise ValueError(f"Category not found: {category_type}")
        
        category.ignored_words = [w.lower().strip() for w in ignored_words]
        category.updated_at = datetime.utcnow()
        await category.save()
        
        return category
