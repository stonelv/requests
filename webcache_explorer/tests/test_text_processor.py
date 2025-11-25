"""Test text processing and search functionality."""

import pytest

from webcache_explorer.text_processor import TextProcessor, SearchResult


class TestTextProcessor:
    """Test TextProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create test text processor."""
        return TextProcessor()
    
    def test_extract_text_from_html(self, processor):
        """Test HTML text extraction."""
        html = '''
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Title</h1>
                <p>This is a <strong>test</strong> paragraph.</p>
                <div>Another paragraph with <a href="/link">link</a>.</div>
            </body>
        </html>
        '''
        
        text = processor.extract_text(html)
        
        assert 'Test Page' in text
        assert 'Main Title' in text
        assert 'This is a test paragraph.' in text
        assert 'Another paragraph with link.' in text
        assert '<html>' not in text
        assert '<strong>' not in text
        assert '<a href="/link">' not in text
    
    def test_extract_title_from_html(self, processor):
        """Test HTML title extraction."""
        html = '''
        <html>
            <head>
                <title>Test Page Title</title>
                <meta name="description" content="Test description">
            </head>
            <body>
                <h1>Main Heading</h1>
            </body>
        </html>
        '''
        
        title = processor.extract_title(html)
        
        assert title == 'Test Page Title'
    
    def test_extract_title_fallback_to_h1(self, processor):
        """Test title extraction fallback to h1 when title tag is missing."""
        html = '''
        <html>
            <body>
                <h1>Main Heading</h1>
                <h2>Subheading</h2>
            </body>
        </html>
        '''
        
        title = processor.extract_title(html)
        
        assert title == 'Main Heading'
    
    def test_extract_title_no_title_available(self, processor):
        """Test title extraction when no title is available."""
        html = '''
        <html>
            <body>
                <div>Just some content</div>
            </body>
        </html>
        '''
        
        title = processor.extract_title(html)
        
        assert title == 'Untitled'
    
    def test_clean_text(self, processor):
        """Test text cleaning."""
        text = '''
        This   is   some    text   with
        multiple   spaces   and   newlines.
        
        
        And   extra   spaces.
        '''
        
        cleaned = processor.clean_text(text)
        
        assert 'This is some text with multiple spaces and newlines.' in cleaned
        assert 'And extra spaces.' in cleaned
        assert '   ' not in cleaned
        assert '\n\n' not in cleaned
    
    def test_tokenize_text(self, processor):
        """Test text tokenization."""
        text = "This is a test sentence with punctuation! And numbers 123."
        
        tokens = processor.tokenize(text)
        
        assert 'this' in tokens
        assert 'is' in tokens
        assert 'test' in tokens
        assert 'sentence' in tokens
        assert 'punctuation' in tokens
        assert 'and' in tokens
        assert 'numbers' in tokens
        assert '123' in tokens
        
        # Check that tokens are lowercase
        assert all(token.islower() or token.isdigit() for token in tokens)
    
    def test_extract_keywords(self, processor):
        """Test keyword extraction."""
        text = '''
        Python is a programming language. Python programming is popular.
        JavaScript is another programming language. JavaScript programming is also popular.
        '''
        
        keywords = processor.extract_keywords(text, top_k=5)
        
        assert len(keywords) == 5
        assert 'python' in keywords
        assert 'programming' in keywords
        assert 'javascript' in keywords
        assert 'language' in keywords
        assert 'popular' in keywords
    
    def test_calculate_relevance_score(self, processor):
        """Test relevance score calculation."""
        text = "Python programming language tutorial guide"
        query = "python tutorial"
        
        score = processor.calculate_relevance_score(text, query)
        
        assert score > 0
        assert score <= 1.0
    
    def test_calculate_relevance_score_exact_match(self, processor):
        """Test relevance score for exact match."""
        text = "Python programming"
        query = "python programming"
        
        score = processor.calculate_relevance_score(text, query)
        
        assert score == 1.0
    
    def test_calculate_relevance_score_no_match(self, processor):
        """Test relevance score for no match."""
        text = "JavaScript programming"
        query = "python tutorial"
        
        score = processor.calculate_relevance_score(text, query)
        
        assert score == 0.0
    
    def test_generate_summary(self, processor):
        """Test summary generation."""
        text = '''
        Python is a high-level programming language. It is widely used for web development,
        data analysis, artificial intelligence, and scientific computing. Python has a simple
        syntax that makes it easy to learn for beginners. The language supports multiple
        programming paradigms including object-oriented, procedural, and functional programming.
        '''
        
        summary = processor.generate_summary(text, max_sentences=2)
        
        assert len(summary.split('.')) <= 2
        assert 'Python' in summary
        assert len(summary) < len(text)
    
    def test_search_content_single_result(self, processor):
        """Test searching content with single result."""
        cache_entries = [
            {
                'url': 'https://python.org',
                'content': 'Python is a programming language. It is popular for web development.',
                'title': 'Python Official Website',
                'status_code': 200,
                'fetch_time': 1.5,
                'content_hash': 'hash1'
            },
            {
                'url': 'https://javascript.com',
                'content': 'JavaScript is a programming language for web browsers.',
                'title': 'JavaScript Info',
                'status_code': 200,
                'fetch_time': 1.2,
                'content_hash': 'hash2'
            }
        ]
        
        results = processor.search_content(cache_entries, 'python programming', top_k=1)
        
        assert len(results) == 1
        assert results[0].url == 'https://python.org'
        assert results[0].title == 'Python Official Website'
        assert results[0].relevance_score > 0
        assert 'Python' in results[0].summary
    
    def test_search_content_multiple_results(self, processor):
        """Test searching content with multiple results."""
        cache_entries = [
            {
                'url': 'https://python.org',
                'content': 'Python is a programming language.',
                'title': 'Python',
                'status_code': 200,
                'fetch_time': 1.5,
                'content_hash': 'hash1'
            },
            {
                'url': 'https://python-tutorial.net',
                'content': 'Python tutorial for beginners. Learn programming.',
                'title': 'Python Tutorial',
                'status_code': 200,
                'fetch_time': 1.2,
                'content_hash': 'hash2'
            },
            {
                'url': 'https://javascript.com',
                'content': 'JavaScript programming language.',
                'title': 'JavaScript',
                'status_code': 200,
                'fetch_time': 1.0,
                'content_hash': 'hash3'
            }
        ]
        
        results = processor.search_content(cache_entries, 'python', top_k=2)
        
        assert len(results) == 2
        # Results should be sorted by relevance
        assert 'python' in results[0].url or 'python' in results[0].title.lower()
        assert 'python' in results[1].url or 'python' in results[1].title.lower()
    
    def test_search_content_no_results(self, processor):
        """Test searching content with no matching results."""
        cache_entries = [
            {
                'url': 'https://python.org',
                'content': 'Python is a programming language.',
                'title': 'Python',
                'status_code': 200,
                'fetch_time': 1.5,
                'content_hash': 'hash1'
            }
        ]
        
        results = processor.search_content(cache_entries, 'javascript', top_k=1)
        
        assert len(results) == 0
    
    def test_search_content_with_failed_entries(self, processor):
        """Test searching content that includes failed entries."""
        cache_entries = [
            {
                'url': 'https://python.org',
                'content': 'Python is a programming language.',
                'title': 'Python',
                'status_code': 200,
                'fetch_time': 1.5,
                'content_hash': 'hash1'
            },
            {
                'url': 'https://failed.com',
                'error_message': 'Connection timeout',
                'content': None,
                'title': 'Failed Page',
                'status_code': 0,
                'fetch_time': 30.0,
                'content_hash': ''
            }
        ]
        
        results = processor.search_content(cache_entries, 'python', top_k=1)
        
        assert len(results) == 1
        assert results[0].url == 'https://python.org'
    
    def test_search_result_dataclass(self):
        """Test SearchResult data class."""
        result = SearchResult(
            url='https://example.com',
            title='Example Page',
            relevance_score=0.85,
            summary='This is a summary.'
        )
        
        assert result.url == 'https://example.com'
        assert result.title == 'Example Page'
        assert result.relevance_score == 0.85
        assert result.summary == 'This is a summary.'
        
        # Test string representation
        str_repr = str(result)
        assert 'https://example.com' in str_repr
        assert 'Example Page' in str_repr
        assert '0.85' in str_repr