#!/usr/bin/env python3
"""
Example usage of the Excel DataFrame Processor.
This script demonstrates how to use the SQL parser and DataFrame manager programmatically.
"""

from excel_processor.sql_parser import SQLParser
from excel_processor.dataframe_manager import DataFrameManager
from pathlib import Path

def main():
    """Demonstrate the Excel DataFrame Processor functionality."""
    
    print("🔍 Excel DataFrame Processor - Example Usage")
    print("=" * 50)
    
    # Check if sample data exists
    sample_dir = Path('sample_data')
    if not sample_dir.exists():
        print("❌ Sample data directory not found!")
        print("Please run: python create_sample_data.py")
        return
    
    try:
        # Initialize components
        print("📚 Initializing components...")
        parser = SQLParser()
        df_manager = DataFrameManager(sample_dir)
        
        # Note: QueryExecutor and ResultFormatter will be implemented in later tasks
        # For now, we'll demonstrate the parser and DataFrame manager
        
        print("✅ Components initialized successfully!")
        print()
        
        # Demonstrate SQL parsing
        print("🔍 SQL Parser Examples:")
        print("-" * 30)
        
        example_queries = [
            "SELECT * FROM employees.staff",
            "SELECT name, salary FROM employees.staff WHERE salary > 70000",
            "SELECT e.name, o.amount FROM employees.staff e, orders.sales_data o WHERE e.id = o.employee_id",
            "SELECT * FROM products.catalog ORDER BY price DESC",
            "SELECT name, department FROM employees.staff > output.csv"
        ]
        
        for i, query in enumerate(example_queries, 1):
            print(f"{i}. Query: {query}")
            try:
                parsed = parser.parse(query)
                print(f"   ✅ Parsed successfully!")
                print(f"   📊 SELECT: {len(parsed.select_node.columns) if parsed.select_node else 0} columns")
                print(f"   📁 FROM: {len(parsed.from_node.tables) if parsed.from_node else 0} tables")
                print(f"   🔍 WHERE: {'Yes' if parsed.where_node else 'No'}")
                print(f"   📤 Export: {parsed.output_file if parsed.output_file else 'No'}")
            except Exception as e:
                print(f"   ❌ Parse error: {e}")
            print()
        
        # Demonstrate DataFrame manager
        print("📊 DataFrame Manager Examples:")
        print("-" * 35)
        
        # Scan database directory
        print("1. Scanning database directory...")
        db_info = df_manager.get_database_info()
        print(f"   📁 Directory: {db_info.directory_path}")
        print(f"   📄 Total files: {db_info.total_files}")
        print(f"   💾 Loaded files: {db_info.loaded_files}")
        print()
        
        # List files and sheets
        print("2. Available files and sheets:")
        files_and_sheets = df_manager.list_all_files_and_sheets()
        for file_name, sheets in files_and_sheets.items():
            print(f"   📄 {file_name}")
            for sheet in sheets:
                print(f"      📋 {sheet}")
        print()
        
        # Load a specific file
        print("3. Loading employees.xlsx...")
        try:
            excel_file = df_manager.load_excel_file("employees.xlsx")
            print(f"   ✅ Loaded successfully!")
            print(f"   📋 Sheets: {', '.join(excel_file.get_sheet_names())}")
            print(f"   💾 Memory usage: {excel_file.memory_usage:.2f} MB")
            print()
            
            # Get a specific DataFrame
            print("4. Getting staff sheet data...")
            df = df_manager.get_dataframe("employees.xlsx", "staff")
            print(f"   📊 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            print(f"   📋 Columns: {', '.join(df.columns.tolist())}")
            print()
            
            # Show first few rows
            print("5. Sample data (first 3 rows):")
            print(df.head(3).to_string(index=False))
            print()
            
        except Exception as e:
            print(f"   ❌ Error loading file: {e}")
        
        # Memory usage
        print("6. Memory usage:")
        memory_info = df_manager.get_memory_usage()
        print(f"   💾 Total: {memory_info['total_mb']:.2f} MB")
        print(f"   📊 Usage: {memory_info['usage_percent']:.1f}%")
        print(f"   📄 Files loaded: {len(memory_info['files'])}")
        print()
        
        print("🎉 Example completed successfully!")
        print()
        print("To start the interactive REPL:")
        print(f"  uv run python -m excel_processor --db {sample_dir}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()