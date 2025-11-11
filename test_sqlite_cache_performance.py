#!/usr/bin/env python3
"""
Performance comparison: With and Without SQLite Cache
Demonstrates the speed improvements from SQLite caching
"""

import time
import sys
from pathlib import Path

def format_time(seconds):
    """Format time in human-readable format"""
    if seconds < 1:
        return f"{seconds*1000:.2f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.2f}s"

def test_without_cache():
    """Test performance WITHOUT SQLite cache"""
    print("\n" + "="*70)
    print("🐌 TEST 1: WITHOUT SQLite Cache (Traditional pandas)")
    print("="*70)
    
    from excel_processor.notebook import ExcelProcessor
    
    # Initialize without cache
    processor = ExcelProcessor('sample_data', memory_limit_mb=2048.0, use_sqlite_cache=False)
    
    # Load database
    print("\n📥 Loading database...")
    start = time.time()
    processor.load_db()
    load_time = time.time() - start
    print(f"✅ Loaded in {format_time(load_time)}")
    
    # Run test queries
    queries = [
        ("SELECT COUNT(*) FROM large_employees.employees", "Count 100K employees"),
        ("SELECT * FROM large_employees.employees WHERE salary > 100000", "Filter high earners"),
        ("SELECT * FROM large_sales.transactions WHERE total_amount > 1000 LIMIT 1000", "Filter sales"),
        ("SELECT * FROM large_timeseries.default WHERE status = 'ERROR' LIMIT 1000", "Filter time series"),
    ]
    
    results = []
    for query, desc in queries:
        print(f"\n🔍 {desc}")
        print(f"   Query: {query[:60]}...")
        
        start = time.time()
        try:
            result = processor.query(query)
            elapsed = time.time() - start
            print(f"   ✅ {format_time(elapsed)} - {len(result):,} rows")
            results.append((desc, elapsed, len(result)))
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append((desc, 0, 0))
    
    return load_time, results

def test_with_cache():
    """Test performance WITH SQLite cache"""
    print("\n" + "="*70)
    print("🚀 TEST 2: WITH SQLite Cache (Optimized)")
    print("="*70)
    
    from excel_processor.notebook import ExcelProcessor
    
    # Initialize with cache
    processor = ExcelProcessor('sample_data', memory_limit_mb=2048.0, use_sqlite_cache=True)
    
    # Load database (will create SQLite cache)
    print("\n📥 Loading database and creating SQLite cache...")
    start = time.time()
    processor.load_db()
    load_time = time.time() - start
    print(f"✅ Loaded and cached in {format_time(load_time)}")
    
    # Show cache stats
    cache_stats = processor.get_cache_stats()
    if cache_stats.get('enabled'):
        print(f"\n📦 Cache Statistics:")
        print(f"   Cached files: {cache_stats['cached_files']}")
        print(f"   Total cache size: {cache_stats['total_size_mb']:.2f} MB")
    
    # Run test queries (should be much faster)
    queries = [
        ("SELECT COUNT(*) FROM large_employees.employees", "Count 100K employees"),
        ("SELECT * FROM large_employees.employees WHERE salary > 100000", "Filter high earners"),
        ("SELECT * FROM large_sales.transactions WHERE total_amount > 1000 LIMIT 1000", "Filter sales"),
        ("SELECT * FROM large_timeseries.default WHERE status = 'ERROR' LIMIT 1000", "Filter time series"),
    ]
    
    results = []
    for query, desc in queries:
        print(f"\n🔍 {desc}")
        print(f"   Query: {query[:60]}...")
        
        start = time.time()
        try:
            result = processor.query(query)
            elapsed = time.time() - start
            print(f"   ✅ {format_time(elapsed)} - {len(result):,} rows")
            results.append((desc, elapsed, len(result)))
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append((desc, 0, 0))
    
    return load_time, results

def compare_results(without_cache, with_cache):
    """Compare and display performance improvements"""
    load_time_no_cache, results_no_cache = without_cache
    load_time_with_cache, results_with_cache = with_cache
    
    print("\n" + "="*70)
    print("📊 PERFORMANCE COMPARISON")
    print("="*70)
    
    print(f"\n{'Operation':<40} {'Without Cache':<15} {'With Cache':<15} {'Speedup':<10}")
    print("-"*70)
    
    # Load time comparison
    if load_time_no_cache > 0:
        speedup = load_time_no_cache / load_time_with_cache if load_time_with_cache > 0 else 0
        print(f"{'Database Load':<40} {format_time(load_time_no_cache):<15} {format_time(load_time_with_cache):<15} {speedup:.2f}x")
    
    # Query comparisons
    for i, (desc, _, _) in enumerate(results_no_cache):
        time_no_cache = results_no_cache[i][1]
        time_with_cache = results_with_cache[i][1]
        
        if time_no_cache > 0 and time_with_cache > 0:
            speedup = time_no_cache / time_with_cache
            speedup_str = f"{speedup:.2f}x" if speedup > 1 else f"{1/speedup:.2f}x slower"
            print(f"{desc:<40} {format_time(time_no_cache):<15} {format_time(time_with_cache):<15} {speedup_str:<10}")
    
    print("-"*70)
    
    # Calculate total time
    total_no_cache = load_time_no_cache + sum(r[1] for r in results_no_cache)
    total_with_cache = load_time_with_cache + sum(r[1] for r in results_with_cache)
    
    if total_no_cache > 0 and total_with_cache > 0:
        overall_speedup = total_no_cache / total_with_cache
        print(f"{'TOTAL TIME':<40} {format_time(total_no_cache):<15} {format_time(total_with_cache):<15} {overall_speedup:.2f}x")
    
    print("\n🎯 Key Insights:")
    if overall_speedup > 1:
        print(f"   ✅ SQLite cache provides {overall_speedup:.1f}x overall speedup")
        print(f"   ✅ Queries are {overall_speedup:.1f}x faster on average")
        print(f"   ✅ Recommended for datasets > 10MB")
    else:
        print(f"   ℹ️  Cache overhead for small datasets")
        print(f"   ℹ️  Benefits increase with larger files and repeated queries")

def main():
    """Main test runner"""
    print("="*70)
    print("🧪 SQLite Cache Performance Testing")
    print("="*70)
    print()
    print("This test compares query performance with and without SQLite caching")
    print("Testing with large datasets:")
    print("  📊 100,000 employee records")
    print("  📊 200,000 sales transactions")
    print("  📄 500,000 time series data points")
    print()
    
    # Check if large files exist
    sample_dir = Path('sample_data')
    required_files = ['large_employees.xlsx', 'large_sales.xlsx', 'large_timeseries.csv']
    
    missing_files = [f for f in required_files if not (sample_dir / f).exists()]
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        print(f"   Run: python create_large_sample_data.py")
        sys.exit(1)
    
    # Run tests
    try:
        # Test without cache
        without_cache_results = test_without_cache()
        
        # Small delay
        time.sleep(2)
        
        # Test with cache
        with_cache_results = test_with_cache()
        
        # Compare results
        compare_results(without_cache_results, with_cache_results)
        
        print("\n" + "="*70)
        print("✅ Performance testing completed!")
        print("="*70)
        print()
        print("💡 Recommendations:")
        print("   • Enable SQLite cache for files > 5MB")
        print("   • Cache provides biggest benefit for repeated queries")
        print("   • First load creates cache (one-time cost)")
        print("   • Subsequent queries are significantly faster")
        print()
        print("🔧 Enable caching:")
        print("   processor = ExcelProcessor('data', use_sqlite_cache=True)")
        print()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
