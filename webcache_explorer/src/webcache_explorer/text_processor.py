"""Text processing and search functionality for WebCache Explorer."""

import html
import logging
import re
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from html.parser import HTMLParser

from bs4 import BeautifulSoup


@dataclass
class SearchResult:
    """Search result with relevance score."""
    url: str
    title: Optional[str]
    snippet: str
    relevance_score: float
    matched_keywords: List[str]
    content_length: int


class TextProcessor:
    """Processes web content for text extraction and search."""
    
    def __init__(self, config):
        """Initialize text processor.
        
        Args:
            config: Configuration object.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Common stop words to filter out
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'or', 'but', 'not', 'this', 'that',
            'these', 'those', 'they', 'them', 'their', 'we', 'us', 'our',
            'you', 'your', 'i', 'me', 'my', 'mine'
        }
    
    def extract_text_from_html(self, html_content: str) -> Tuple[str, Optional[str]]:
        """Extract clean text and title from HTML content.
        
        Args:
            html_content: Raw HTML content.
            
        Returns:
            Tuple of (clean_text, title).
        """
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Extract title
            title = None
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            else:
                # Try h1 tag as fallback
                h1_tag = soup.find('h1')
                if h1_tag:
                    title = h1_tag.get_text().strip()
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Decode HTML entities
            text = html.unescape(text)
            
            return text, title
            
        except Exception as e:
            self.logger.error(f"Failed to extract text from HTML: {e}")
            # Fallback: simple regex-based text extraction
            return self._simple_html_to_text(html_content), None
    
    def _simple_html_to_text(self, html_content: str) -> str:
        """Simple HTML to text conversion using regex."""
        try:
            # Remove script and style content
            text = re.sub(r'<(script|style).*?>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            
            # Decode HTML entities
            text = html.unescape(text)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
            
        except Exception as e:
            self.logger.error(f"Failed in simple HTML conversion: {e}")
            return ""
    
    def tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words.
        
        Args:
            text: Input text.
            
        Returns:
            List of tokens.
        """
        if not text:
            return []
        
        # Convert to lowercase and extract words
        text = text.lower()
        
        # Remove punctuation and split into words
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        
        # Filter out stop words and short words
        filtered_words = [
            word for word in words 
            if len(word) >= self.config.min_keyword_length and word not in self.stop_words
        ]
        
        return filtered_words
    
    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[Tuple[str, int]]:
        """Extract keywords from text based on frequency.
        
        Args:
            text: Input text.
            max_keywords: Maximum number of keywords to return.
            
        Returns:
            List of (keyword, frequency) tuples.
        """
        tokens = self.tokenize_text(text)
        
        if not tokens:
            return []
        
        # Count word frequencies
        word_counts = Counter(tokens)
        
        # Return most common words
        return word_counts.most_common(max_keywords)
    
    def calculate_relevance_score(self, text: str, keywords: List[str]) -> float:
        """Calculate relevance score of text for given keywords.
        
        Args:
            text: Text to score.
            keywords: List of keywords to search for.
            
        Returns:
            Relevance score between 0 and 1.
        """
        if not text or not keywords:
            return 0.0
        
        text_lower = text.lower()
        total_keywords = len(keywords)
        
        # Count keyword matches
        matches = 0
        keyword_positions = {}
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = text_lower.count(keyword_lower)
            if count > 0:
                matches += 1
                # Store positions for snippet generation
                positions = []
                start = 0
                while True:
                    pos = text_lower.find(keyword_lower, start)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start = pos + 1
                keyword_positions[keyword] = positions
        
        if matches == 0:
            return 0.0
        
        # Calculate score based on:
        # - Keyword coverage (how many keywords matched)
        # - Keyword density (how often keywords appear)
        # - Text length factor (prefer reasonable text length)
        
        coverage_score = matches / total_keywords
        
        # Count total keyword occurrences
        total_occurrences = sum(len(positions) for positions in keyword_positions.values())
        density_score = min(total_occurrences / (len(text) / 100), 1.0)  # Normalize to text length
        
        # Length factor: prefer texts that are not too short or too long
        text_length = len(text)
        if text_length < 100:
            length_factor = text_length / 100  # Penalize very short texts
        elif text_length > 10000:
            length_factor = 0.8  # Slight penalty for very long texts
        else:
            length_factor = 1.0
        
        # Combine scores
        final_score = (coverage_score * 0.5 + density_score * 0.3 + length_factor * 0.2)
        
        return min(final_score, 1.0)
    
    def generate_snippet(self, text: str, keywords: List[str], max_length: int = 200) -> str:
        """Generate text snippet highlighting keywords.
        
        Args:
            text: Original text.
            keywords: Keywords to highlight.
            max_length: Maximum snippet length.
            
        Returns:
            Generated snippet.
        """
        if not text:
            return ""
        
        if len(text) <= max_length:
            return self._highlight_keywords(text, keywords)
        
        # Find best position for snippet based on keyword density
        text_lower = text.lower()
        best_score = 0
        best_start = 0
        
        # Try different starting positions
        step = max(1, len(text) // 100)  # Check every 1% of text
        for start in range(0, len(text) - max_length, step):
            end = min(start + max_length, len(text))
            snippet_text = text[start:end]
            score = self.calculate_relevance_score(snippet_text, keywords)
            
            if score > best_score:
                best_score = score
                best_start = start
        
        # Generate snippet
        snippet = text[best_start:best_start + max_length]
        
        # Add ellipsis if needed
        if best_start > 0:
            snippet = "..." + snippet
        if best_start + max_length < len(text):
            snippet = snippet + "..."
        
        return self._highlight_keywords(snippet, keywords)
    
    def _highlight_keywords(self, text: str, keywords: List[str]) -> str:
        """Highlight keywords in text.
        
        Args:
            text: Original text.
            keywords: Keywords to highlight.
            
        Returns:
            Text with highlighted keywords.
        """
        if not keywords:
            return text
        
        highlighted = text
        for keyword in keywords:
            # Case-insensitive replacement
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            highlighted = pattern.sub(f"**{keyword}**", highlighted)
        
        return highlighted
    
    def search_content(self, cache_manager, query: str, max_results: int = None) -> List[SearchResult]:
        """Search cached content for query.
        
        Args:
            cache_manager: CacheManager instance.
            query: Search query.
            max_results: Maximum number of results. Uses config default if None.
            
        Returns:
            List of SearchResult objects sorted by relevance.
        """
        if not query:
            return []
        
        if max_results is None:
            max_results = self.config.max_search_results
        
        # Tokenize query
        keywords = self.tokenize_text(query)
        if not keywords:
            return []
        
        self.logger.info(f"Searching for '{query}' with keywords: {keywords}")
        
        results = []
        
        # Get all cached URLs
        urls = cache_manager.get_successful_urls()
        
        for url in urls:
            cached_data = cache_manager.retrieve(url)
            if not cached_data or not cached_data.get('content'):
                continue
            
            # Extract text from HTML
            text, title = self.extract_text_from_html(cached_data['content'])
            if not text:
                continue
            
            # Calculate relevance score
            relevance_score = self.calculate_relevance_score(text, keywords)
            if relevance_score == 0:
                continue
            
            # Generate snippet
            snippet = self.generate_snippet(text, keywords)
            
            # Create search result
            result = SearchResult(
                url=url,
                title=title or url,
                snippet=snippet,
                relevance_score=relevance_score,
                matched_keywords=[kw for kw in keywords if kw.lower() in text.lower()],
                content_length=len(text)
            )
            
            results.append(result)
        
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Return top results
        return results[:max_results]
    
    def get_content_summary(self, content: str, max_words: int = 50) -> str:
        """Generate a summary of content.
        
        Args:
            content: Content to summarize.
            max_words: Maximum words in summary.
            
        Returns:
            Content summary.
        """
        if not content:
            return ""
        
        # Extract text from HTML if needed
        if '<' in content and '>' in content:
            text, _ = self.extract_text_from_html(content)
        else:
            text = content
        
        if not text:
            return ""
        
        words = text.split()
        if len(words) <= max_words:
            return text
        
        return ' '.join(words[:max_words]) + "..."