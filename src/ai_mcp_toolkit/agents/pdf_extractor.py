"""PDF text extractor agent for extracting text from PDF files."""

import time
import io
from typing import Any, Dict, List
from mcp.types import Tool

from .base_agent import BaseAgent


class PDFExtractorAgent(BaseAgent):
    """Agent for extracting text content from PDF files."""

    def __init__(self, config):
        """Initialize the PDF extractor agent."""
        super().__init__(config)

    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this agent."""
        return [
            Tool(
                name="extract_pdf_text",
                description="Extract text content from a PDF file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pdf_content": {
                            "type": "string",
                            "description": "Base64 encoded PDF file content or binary data as string"
                        },
                        "page_range": {
                            "type": "string",
                            "description": "Optional page range to extract (e.g., '1-5' or 'all')",
                            "default": "all"
                        },
                        "include_metadata": {
                            "type": "boolean",
                            "description": "Whether to include PDF metadata in the output",
                            "default": False
                        }
                    },
                    "required": ["pdf_content"]
                }
            )
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool with given arguments and return result."""
        start_time = time.time()
        
        try:
            if tool_name == "extract_pdf_text":
                result = await self._extract_pdf_text(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            duration = time.time() - start_time
            self.log_execution(tool_name, arguments, duration)
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _extract_pdf_text(self, arguments: Dict[str, Any]) -> str:
        """Extract text from PDF content."""
        try:
            from pypdf import PdfReader
            import base64
        except ImportError:
            raise ValueError("pypdf library not installed. Run: pip install pypdf")
        
        pdf_content = arguments.get("pdf_content")
        page_range = arguments.get("page_range", "all")
        include_metadata = arguments.get("include_metadata", False)
        
        if not pdf_content:
            raise ValueError("pdf_content is required")
        
        try:
            # Try to decode if it's base64
            try:
                pdf_bytes = base64.b64decode(pdf_content)
            except Exception:
                # If decode fails, assume it's already bytes
                pdf_bytes = pdf_content.encode() if isinstance(pdf_content, str) else pdf_content
            
            # Read PDF
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            
            # Extract metadata if requested
            metadata_text = ""
            if include_metadata:
                metadata = reader.metadata
                if metadata:
                    metadata_text = "PDF Metadata:\n"
                    if metadata.title:
                        metadata_text += f"Title: {metadata.title}\n"
                    if metadata.author:
                        metadata_text += f"Author: {metadata.author}\n"
                    if metadata.subject:
                        metadata_text += f"Subject: {metadata.subject}\n"
                    if metadata.creator:
                        metadata_text += f"Creator: {metadata.creator}\n"
                    metadata_text += f"Pages: {len(reader.pages)}\n\n"
            
            # Determine pages to extract
            total_pages = len(reader.pages)
            if page_range == "all":
                pages_to_extract = range(total_pages)
            else:
                try:
                    # Parse page range like "1-5" or "3"
                    if "-" in page_range:
                        start, end = page_range.split("-")
                        pages_to_extract = range(int(start) - 1, min(int(end), total_pages))
                    else:
                        page_num = int(page_range) - 1
                        pages_to_extract = range(page_num, page_num + 1)
                except ValueError:
                    raise ValueError(f"Invalid page range format: {page_range}")
            
            # Extract text from pages
            extracted_text = []
            for page_num in pages_to_extract:
                if 0 <= page_num < total_pages:
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    if text.strip():
                        extracted_text.append(f"--- Page {page_num + 1} ---\n{text}")
            
            if not extracted_text:
                return "No text content found in the PDF."
            
            result = metadata_text + "\n\n".join(extracted_text)
            
            self.logger.info(f"Successfully extracted {len(result)} characters from PDF ({len(extracted_text)} pages)")
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting PDF text: {e}")
            raise ValueError(f"Failed to extract PDF text: {str(e)}")

    def extract_text_from_bytes(self, pdf_bytes: bytes, page_range: str = "all", include_metadata: bool = False) -> str:
        """
        Synchronous helper method to extract text from PDF bytes.
        This is useful for direct integration with resource manager.
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ValueError("pypdf library not installed. Run: pip install pypdf")
        
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            
            # Extract metadata if requested
            metadata_text = ""
            if include_metadata:
                metadata = reader.metadata
                if metadata:
                    metadata_text = "PDF Metadata:\n"
                    if metadata.title:
                        metadata_text += f"Title: {metadata.title}\n"
                    if metadata.author:
                        metadata_text += f"Author: {metadata.author}\n"
                    if metadata.subject:
                        metadata_text += f"Subject: {metadata.subject}\n"
                    metadata_text += f"Pages: {len(reader.pages)}\n\n"
            
            # Extract all pages
            total_pages = len(reader.pages)
            extracted_text = []
            
            for page_num in range(total_pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    extracted_text.append(f"--- Page {page_num + 1} ---\n{text}")
            
            if not extracted_text:
                return "No text content found in the PDF."
            
            result = metadata_text + "\n\n".join(extracted_text)
            
            self.logger.info(f"Extracted {len(result)} characters from PDF ({total_pages} pages)")
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting PDF text: {e}")
            raise ValueError(f"Failed to extract PDF text: {str(e)}")
