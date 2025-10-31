"""CSV processor for extracting structured data from CSV files."""

import csv
import io
import logging
from typing import Dict, Any, List

from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class CSVProcessor(BaseProcessor):
    """Process CSV files and extract structured metadata."""
    
    async def process(self, file_bytes: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process CSV file and extract metadata and row-level chunks.
        
        Args:
            file_bytes: CSV file content
            metadata: Initial metadata (filename, mime_type, etc.)
            
        Returns:
            Dict with file_metadata and chunks
        """
        try:
            # Decode CSV
            text_content = file_bytes.decode('utf-8')
            csv_file = io.StringIO(text_content)
            
            # Parse CSV
            reader = csv.DictReader(csv_file)
            rows = list(reader)
            
            if not rows:
                return {
                    'file_metadata': {
                        'file_type': 'csv',
                        'size_bytes': len(file_bytes),
                        'row_count': 0,
                        'columns': [],
                    },
                    'chunks': []
                }
            
            # Get schema
            columns = list(rows[0].keys())
            
            # Aggregate all text and numeric data
            all_text = " ".join([" ".join(row.values()) for row in rows])
            all_amounts = []
            dates = []
            entities = []
            keywords = set()
            
            # Analyze rows
            for row in rows:
                for col, value in row.items():
                    if not value:
                        continue
                    
                    # Extract amounts
                    row_amounts = self.extract_amounts(value)
                    all_amounts.extend(row_amounts)
                    
                    # Extract dates
                    row_dates = self.extract_dates(value)
                    dates.extend(row_dates)
                    
                    # Extract entities
                    row_entities = self.extract_entities(value)
                    entities.extend(row_entities)
                    
                    # Add as keyword if looks like ID or specific value
                    if value and len(value) < 50 and not value.replace('.', '').replace(',', '').isdigit():
                        keywords.add(value.lower())
            
            # Calculate statistics
            min_amount = min(all_amounts) if all_amounts else None
            max_amount = max(all_amounts) if all_amounts else None
            
            currency = self.extract_currency(all_text)
            
            # Identify vendor if possible
            vendor = None
            if 'vendor' in [c.lower() for c in columns]:
                vendor_col = next((c for c in columns if c.lower() == 'vendor'), None)
                if vendor_col:
                    vendors = [row[vendor_col] for row in rows if row.get(vendor_col)]
                    if vendors:
                        vendor = self.normalize_vendor(vendors[0])
            
            # Build file-level metadata
            file_metadata = {
                'file_type': 'csv',
                'size_bytes': len(file_bytes),
                'row_count': len(rows),
                'columns': columns,
                'vendor': vendor,
                'currency': currency,
                'amounts_cents': all_amounts[:100],  # Limit to first 100
                'entities': list(set(entities))[:50],  # Unique, limited
                'keywords': list(keywords)[:100],
                'dates': dates[:50],
                'min_amount_cents': min_amount,
                'max_amount_cents': max_amount,
                'summary': f"CSV with {len(rows)} rows and {len(columns)} columns",
            }
            
            # Create row-level chunks (sample first 1000 rows)
            chunks = []
            for idx, row in enumerate(rows[:1000]):
                row_text = " ".join([f"{k}: {v}" for k, v in row.items() if v])
                
                # Extract structured data from row
                row_amounts = self.extract_amounts(row_text)
                row_entities = self.extract_entities(row_text)
                row_dates = self.extract_dates(row_text)
                
                chunk = {
                    'chunk_type': 'row',
                    'chunk_index': idx,
                    'row_number': idx + 1,  # 1-indexed
                    'text': row_text,
                    'row_data': row,
                    'currency': currency if row_amounts else None,
                    'amounts_cents': row_amounts,
                    'entities': row_entities,
                    'dates': row_dates,
                }
                
                chunks.append(chunk)
            
            self.logger.info(
                f"Processed CSV: {len(rows)} rows, {len(columns)} columns, "
                f"{len(all_amounts)} amounts extracted"
            )
            
            return {
                'file_metadata': file_metadata,
                'chunks': chunks
            }
            
        except Exception as e:
            self.logger.error(f"Error processing CSV: {e}", exc_info=True)
            return {
                'file_metadata': {
                    'file_type': 'csv',
                    'size_bytes': len(file_bytes),
                },
                'chunks': []
            }
