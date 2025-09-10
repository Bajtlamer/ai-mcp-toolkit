"""URL content fetcher utility for extracting clean text from web pages."""

import asyncio
import aiohttp
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urljoin
import logging
from bs4 import BeautifulSoup, Comment
import chardet


logger = logging.getLogger(__name__)


class URLContentFetcher:
    """Utility class for fetching and extracting clean text content from URLs."""
    
    def __init__(self, timeout: int = 30, max_size: int = 5 * 1024 * 1024):
        """
        Initialize the URL content fetcher.
        
        Args:
            timeout: Request timeout in seconds
            max_size: Maximum content size to download (in bytes)
        """
        self.timeout = timeout
        self.max_size = max_size
        
    async def fetch_content(self, url: str) -> Dict[str, Any]:
        """
        Fetch and extract clean text content from a URL.
        
        Args:
            url: The URL to fetch content from
            
        Returns:
            Dictionary with extracted content information
            
        Raises:
            ValueError: If URL is invalid or content cannot be extracted
            aiohttp.ClientError: If network request fails
        """
        # Validate URL
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")
            
        logger.info(f"Fetching content from URL: {url}")
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(
                    url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (compatible; AI-MCP-Toolkit/1.0; +https://github.com/ai-mcp-toolkit)',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                    }
                ) as response:
                    
                    # Check response status
                    if response.status != 200:
                        raise ValueError(f"HTTP {response.status}: Failed to fetch content from {url}")
                    
                    # Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if not any(ct in content_type for ct in ['text/html', 'application/xhtml', 'text/plain']):
                        raise ValueError(f"Unsupported content type: {content_type}")
                    
                    # Check content size
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > self.max_size:
                        raise ValueError(f"Content too large: {content_length} bytes (max: {self.max_size})")
                    
                    # Read content with size limit
                    content = b''
                    async for chunk in response.content.iter_chunked(8192):
                        content += chunk
                        if len(content) > self.max_size:
                            raise ValueError(f"Content too large (exceeded {self.max_size} bytes)")
                    
                    # Detect encoding
                    encoding = self._detect_encoding(content, response.headers.get('content-type'))
                    
                    # Decode content
                    try:
                        html_content = content.decode(encoding)
                    except UnicodeDecodeError:
                        # Fallback to UTF-8 with error handling
                        html_content = content.decode('utf-8', errors='replace')
                    
                    # Extract clean text
                    result = self._extract_text_from_html(html_content, url)
                    
                    logger.info(f"Successfully extracted {len(result['text'])} characters from {url}")
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching {url}: {e}")
            raise ValueError(f"Failed to fetch URL: {str(e)}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            raise ValueError(f"Timeout while fetching URL (>{self.timeout}s)")
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            raise ValueError(f"Error fetching URL: {str(e)}")
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and safe to fetch."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme in ['http', 'https']:
                return False
            if not parsed.netloc:
                return False
            # Basic security check - avoid localhost and private IPs
            if any(host in parsed.netloc.lower() for host in ['localhost', '127.0.0.1', '0.0.0.0']):
                logger.warning(f"Rejecting localhost URL: {url}")
                return False
            return True
        except Exception:
            return False
    
    def _detect_encoding(self, content: bytes, content_type: Optional[str]) -> str:
        """Detect the encoding of HTML content."""
        # First, try to get encoding from content-type header
        if content_type:
            charset_match = re.search(r'charset=([^;]+)', content_type.lower())
            if charset_match:
                return charset_match.group(1).strip('"\'')
        
        # Try to detect from HTML meta tags
        try:
            # Look for charset in first 1024 bytes
            head_content = content[:1024].decode('ascii', errors='ignore').lower()
            
            # HTML5 style: <meta charset="...">
            charset_match = re.search(r'<meta\s+charset=["\']?([^"\'>\s]+)', head_content)
            if charset_match:
                return charset_match.group(1)
            
            # HTML4 style: <meta http-equiv="content-type" content="...; charset=...">
            content_type_match = re.search(
                r'<meta\s+http-equiv=["\']?content-type["\']?\s+content=["\']?[^"\']*charset=([^"\'>\s]+)',
                head_content
            )
            if content_type_match:
                return content_type_match.group(1)
        except:
            pass
        
        # Fall back to chardet detection
        try:
            detected = chardet.detect(content[:4096])  # Only check first 4KB for speed
            if detected and detected.get('confidence', 0) > 0.7:
                return detected['encoding']
        except:
            pass
        
        # Final fallback
        return 'utf-8'
    
    def _extract_text_from_html(self, html: str, url: str) -> Dict[str, Any]:
        """Extract clean text content from HTML."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "noscript"]):
                script.extract()
            
            # Remove comments
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
            
            # Try to find the main content area
            main_content = self._find_main_content(soup)
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else ""
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = ""
            if meta_desc and meta_desc.get('content'):
                description = meta_desc['content'].strip()
            
            # Extract text from main content
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                # Fallback to body content
                body = soup.find('body')
                if body:
                    text = body.get_text(separator=' ', strip=True)
                else:
                    text = soup.get_text(separator=' ', strip=True)
            
            # Clean up the text
            text = self._clean_text(text)
            
            if not text.strip():
                raise ValueError("No readable text content found")
            
            return {
                'text': text,
                'title': title,
                'description': description,
                'url': url,
                'length': len(text),
                'word_count': len(text.split())
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")
            raise ValueError(f"Failed to extract text from HTML: {str(e)}")
    
    def _find_main_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Try to find the main content area of the page."""
        # Common selectors for main content
        main_selectors = [
            'main',
            'article',
            '[role="main"]',
            '.main-content',
            '#main-content',
            '.content',
            '#content',
            '.post-content',
            '.entry-content',
            '.article-content',
            '.story-body',
            '.post-body'
        ]
        
        for selector in main_selectors:
            element = soup.select_one(selector)
            if element:
                return element
        
        # If no main content found, look for the largest content block
        content_blocks = soup.find_all(['div', 'section', 'article'])
        if content_blocks:
            # Find the block with the most text content
            largest_block = max(content_blocks, key=lambda x: len(x.get_text(strip=True)))
            if len(largest_block.get_text(strip=True)) > 100:  # Minimum content threshold
                return largest_block
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common navigation/footer text patterns
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip common navigation patterns
            if any(pattern in line.lower() for pattern in [
                'skip to content',
                'skip to main content',
                'cookie notice',
                'accept cookies',
                'privacy policy',
                'terms of service',
                'sign up',
                'subscribe',
                'newsletter',
                'advertisement'
            ]):
                continue
            
            # Skip very short lines (likely navigation)
            if len(line) < 10:
                continue
                
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()


# Convenience function for simple usage
async def fetch_url_content(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Convenience function to fetch content from a URL.
    
    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with extracted content
    """
    fetcher = URLContentFetcher(timeout=timeout)
    return await fetcher.fetch_content(url)
