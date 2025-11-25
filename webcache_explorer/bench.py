#!/usr/bin/env python3
"""
WebCache Explorer - Performance Benchmarking Script

This script performs performance testing of the web cache explorer
by fetching a set of test URLs and measuring various metrics.
"""

import time
import statistics
import sys
from pathlib import Path
from typing import List, Dict, Any

from webcache_explorer.config import Config
from webcache_explorer.crawler import WebCrawler
from webcache_explorer.cache import CacheManager


class PerformanceBenchmark:
    """Performance benchmarking for WebCache Explorer."""
    
    def __init__(self, config: Config):
        """Initialize benchmark with configuration."""
        self.config = config
        self.results = []
        self.crawler = None
        self.cache_manager = None
    
    def setup(self):
        """Setup benchmark environment."""
        print("Setting up benchmark environment...")
        self.crawler = WebCrawler(config=self.config)
        self.cache_manager = CacheManager(self.config)
        print("✓ Environment setup complete")
    
    def cleanup(self):
        """Cleanup benchmark environment."""
        print("\nCleaning up benchmark environment...")
        # Clear cache for clean benchmark runs
        if self.cache_manager:
            self.cache_manager.clear()
        print("✓ Cleanup complete")
    
    def get_test_urls(self) -> List[str]:
        """Get list of test URLs for benchmarking."""
        return [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml",
            "https://httpbin.org/robots.txt",
            "https://httpbin.org/uuid",
            "https://httpbin.org/base64/SFRUUEJJTiBpcyBhd2Vzb21l",
            "https://httpbin.org/delay/1",
            "https://httpbin.org/status/200",
            "https://httpbin.org/headers",
            "https://httpbin.org/user-agent"
        ]
    
    def measure_single_fetch(self, url: str) -> Dict[str, Any]:
        """Measure performance of fetching a single URL."""
        start_time = time.time()
        
        try:
            result = self.crawler.fetch_url(url)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            return {
                'url': url,
                'success': result['success'],
                'status_code': result.get('status_code'),
                'fetch_time': result['fetch_time'],
                'total_time': total_time,
                'content_size': len(result.get('content', '')) if result.get('content') else 0,
                'error': result.get('error_message')
            }
        except Exception as e:
            end_time = time.time()
            return {
                'url': url,
                'success': False,
                'status_code': None,
                'fetch_time': 0,
                'total_time': end_time - start_time,
                'content_size': 0,
                'error': str(e)
            }
    
    def measure_batch_fetch(self, urls: List[str], max_workers: int) -> Dict[str, Any]:
        """Measure performance of batch fetching URLs."""
        start_time = time.time()
        
        # Temporarily set max_workers for this test
        original_max_workers = self.config.max_workers
        self.config.max_workers = max_workers
        self.crawler = WebCrawler(config=self.config)  # Recreate with new config
        
        try:
            results = self.crawler.fetch_urls(urls)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            successful_results = [r for r in results if r['success']]
            failed_results = [r for r in results if not r['success']]
            
            fetch_times = [r['fetch_time'] for r in successful_results]
            content_sizes = [len(r.get('content', '')) for r in successful_results if r.get('content')]
            
            return {
                'max_workers': max_workers,
                'total_urls': len(urls),
                'successful_fetches': len(successful_results),
                'failed_fetches': len(failed_results),
                'success_rate': len(successful_results) / len(urls),
                'total_time': total_time,
                'avg_fetch_time': statistics.mean(fetch_times) if fetch_times else 0,
                'min_fetch_time': min(fetch_times) if fetch_times else 0,
                'max_fetch_time': max(fetch_times) if fetch_times else 0,
                'total_content_size': sum(content_sizes),
                'avg_content_size': statistics.mean(content_sizes) if content_sizes else 0,
                'requests_per_second': len(successful_results) / total_time if total_time > 0 else 0
            }
        finally:
            # Restore original max_workers
            self.config.max_workers = original_max_workers
            self.crawler = WebCrawler(config=self.config)
    
    def measure_cache_operations(self, urls: List[str]) -> Dict[str, Any]:
        """Measure cache storage and retrieval performance."""
        # First, fetch and cache the URLs
        results = self.crawler.fetch_urls(urls)
        
        # Measure cache storage time
        storage_start = time.time()
        for result in results:
            self.cache_manager.store(result)
        storage_end = time.time()
        storage_time = storage_end - storage_start
        
        # Measure cache retrieval time
        retrieval_start = time.time()
        for url in urls:
            self.cache_manager.retrieve(url)
        retrieval_end = time.time()
        retrieval_time = retrieval_end - retrieval_start
        
        # Get cache stats
        stats = self.cache_manager.get_stats()
        
        return {
            'storage_time': storage_time,
            'retrieval_time': retrieval_time,
            'avg_storage_time_per_entry': storage_time / len(results),
            'avg_retrieval_time_per_entry': retrieval_time / len(urls),
            'cache_stats': stats
        }
    
    def run_single_url_benchmark(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Run benchmark for single URL fetches."""
        print(f"\n📊 Running single URL fetch benchmark ({len(urls)} URLs)...")
        
        results = []
        for i, url in enumerate(urls, 1):
            print(f"  [{i}/{len(urls)}] Fetching: {url}")
            result = self.measure_single_fetch(url)
            results.append(result)
            
            if result['success']:
                print(f"    ✓ Success: {result['fetch_time']:.3f}s, {result['content_size']} bytes")
            else:
                print(f"    ✗ Failed: {result['error']}")
        
        return results
    
    def run_concurrency_benchmark(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Run benchmark for different concurrency levels."""
        print(f"\n🚀 Running concurrency benchmark...")
        
        concurrency_levels = [1, 2, 4, 8]
        results = []
        
        for max_workers in concurrency_levels:
            print(f"  Testing with {max_workers} workers...")
            result = self.measure_batch_fetch(urls, max_workers)
            results.append(result)
            
            print(f"    ✓ Success rate: {result['success_rate']:.1%}")
            print(f"    ✓ Total time: {result['total_time']:.3f}s")
            print(f"    ✓ Requests/sec: {result['requests_per_second']:.2f}")
            print(f"    ✓ Avg fetch time: {result['avg_fetch_time']:.3f}s")
        
        return results
    
    def run_cache_benchmark(self, urls: List[str]) -> Dict[str, Any]:
        """Run cache performance benchmark."""
        print(f"\n💾 Running cache performance benchmark...")
        
        result = self.measure_cache_operations(urls)
        
        print(f"  ✓ Storage time: {result['storage_time']:.3f}s")
        print(f"  ✓ Retrieval time: {result['retrieval_time']:.3f}s")
        print(f"  ✓ Avg storage time per entry: {result['avg_storage_time_per_entry']:.4f}s")
        print(f"  ✓ Avg retrieval time per entry: {result['avg_retrieval_time_per_entry']:.4f}s")
        
        return result
    
    def generate_report(self, single_results: List[Dict], concurrency_results: List[Dict], 
                       cache_results: Dict) -> str:
        """Generate comprehensive benchmark report."""
        report = []
        report.append("=" * 60)
        report.append("WEBCACHE EXPLORER PERFORMANCE BENCHMARK REPORT")
        report.append("=" * 60)
        
        # Single URL fetch statistics
        successful_single = [r for r in single_results if r['success']]
        failed_single = [r for r in single_results if not r['success']]
        
        report.append(f"\n📈 SINGLE URL FETCH STATISTICS")
        report.append(f"Total URLs tested: {len(single_results)}")
        report.append(f"Successful fetches: {len(successful_single)}")
        report.append(f"Failed fetches: {len(failed_single)}")
        report.append(f"Success rate: {len(successful_single)/len(single_results)*100:.1f}%")
        
        if successful_single:
            fetch_times = [r['fetch_time'] for r in successful_single]
            content_sizes = [r['content_size'] for r in successful_single]
            
            report.append(f"\n⏱️  FETCH TIME STATISTICS")
            report.append(f"Average fetch time: {statistics.mean(fetch_times):.3f}s")
            report.append(f"Median fetch time: {statistics.median(fetch_times):.3f}s")
            report.append(f"Min fetch time: {min(fetch_times):.3f}s")
            report.append(f"Max fetch time: {max(fetch_times):.3f}s")
            report.append(f"Standard deviation: {statistics.stdev(fetch_times):.3f}s")
            
            report.append(f"\n📄 CONTENT SIZE STATISTICS")
            report.append(f"Average content size: {statistics.mean(content_sizes):.0f} bytes")
            report.append(f"Median content size: {statistics.median(content_sizes):.0f} bytes")
            report.append(f"Min content size: {min(content_sizes)} bytes")
            report.append(f"Max content size: {max(content_sizes)} bytes")
            report.append(f"Total content size: {sum(content_sizes)} bytes")
        
        # Concurrency benchmark results
        report.append(f"\n🚀 CONCURRENCY BENCHMARK RESULTS")
        for result in concurrency_results:
            report.append(f"\nWorkers: {result['max_workers']}")
            report.append(f"  Success rate: {result['success_rate']:.1%}")
            report.append(f"  Total time: {result['total_time']:.3f}s")
            report.append(f"  Requests/second: {result['requests_per_second']:.2f}")
            report.append(f"  Average fetch time: {result['avg_fetch_time']:.3f}s")
            report.append(f"  Total content size: {result['total_content_size']} bytes")
        
        # Cache performance results
        report.append(f"\n💾 CACHE PERFORMANCE")
        report.append(f"Storage time: {cache_results['storage_time']:.3f}s")
        report.append(f"Retrieval time: {cache_results['retrieval_time']:.3f}s")
        report.append(f"Average storage time per entry: {cache_results['avg_storage_time_per_entry']:.4f}s")
        report.append(f"Average retrieval time per entry: {cache_results['avg_retrieval_time_per_entry']:.4f}s")
        
        cache_stats = cache_results['cache_stats']
        report.append(f"\n📊 CACHE STATISTICS")
        report.append(f"Total entries: {cache_stats['total_entries']}")
        report.append(f"Successful entries: {cache_stats['successful_entries']}")
        report.append(f"Failed entries: {cache_stats['failed_entries']}")
        report.append(f"Success rate: {cache_stats['success_rate']:.1%}")
        report.append(f"Total cache size: {cache_stats['total_size_mb']:.2f} MB")
        report.append(f"Average fetch time: {cache_stats['average_fetch_time']:.3f}s")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def run_benchmark(self):
        """Run complete benchmark suite."""
        print("🚀 Starting WebCache Explorer Performance Benchmark")
        print("=" * 50)
        
        try:
            self.setup()
            
            # Get test URLs
            test_urls = self.get_test_urls()
            print(f"📋 Loaded {len(test_urls)} test URLs")
            
            # Run benchmarks
            single_results = self.run_single_url_benchmark(test_urls)
            concurrency_results = self.run_concurrency_benchmark(test_urls)
            cache_results = self.run_cache_benchmark(test_urls)
            
            # Generate and display report
            report = self.generate_report(single_results, concurrency_results, cache_results)
            print(report)
            
            # Save report to file
            report_file = Path(self.config.data_dir) / "benchmark_report.txt"
            report_file.write_text(report, encoding='utf-8')
            print(f"\n📄 Benchmark report saved to: {report_file}")
            
        finally:
            self.cleanup()


def main():
    """Main entry point for benchmark script."""
    # Load configuration
    config = Config()
    
    # Create benchmark instance and run
    benchmark = PerformanceBenchmark(config)
    benchmark.run_benchmark()


if __name__ == "__main__":
    main()