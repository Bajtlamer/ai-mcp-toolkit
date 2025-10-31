"""File processors for extracting metadata and content from various file types."""

from .base_processor import BaseProcessor
from .pdf_processor import PDFProcessor
from .csv_processor import CSVProcessor
from .image_processor import ImageProcessor
from .text_processor import TextProcessor
from .snippet_processor import SnippetProcessor

__all__ = [
    "BaseProcessor",
    "PDFProcessor",
    "CSVProcessor",
    "ImageProcessor",
    "TextProcessor",
    "SnippetProcessor",
]
