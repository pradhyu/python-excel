#!/usr/bin/env python3
"""Test quoted column names and aliases functionality."""
import subprocess
import sys

def test_quoted_columns_and_aliases():
    """Test all quoted column names and alias functionality."""
    print("🧪 Testing Quoted Column Names and Aliases")
    print("=" * 50)
    
    # Test commands
    commands = [
        # Basic quoted column names
        'SELECT "Full Name", "Annual Salary" FROM spaced_columns.employee_data',
        
        # Column aliases
        'SELECT "Full Name" as employee_name, "Annual Salary" as salary FROM spaced_columns.employee_data',
        
        # Mixed quotes
        "SELECT 'Job Title' as position, \"Performance Rating\" as rating FROM spaced_columns.employee_data",
        
        # Aliases with WHERE clause
        'SELECT "Full Name" as name, "Annual Salary" as salary FROM spaced_columns.employee_data WHERE "Annual Salary" > 70000',
        
        # Window functions with aliases
        'SELECT "Full Name" as employee, "Annual Salary" as salary, ROW_NUMBER() OVER (ORDER BY "Annual Salary" DESC) as rank FROM spaced_columns.employee_data',
        
        # Aggregate functions with aliases
        "SELECT 'Job Title' as position, COUNT(*) as employee_count FROM spaced_columns.employee_data GROUP BY 'Job Title'",
        
        # Complex query with multiple aliases
        'SELECT "Full Name" as name, "Job Title" as role, "Annual Salary" as salary, "Performance Rating" as rating FROM spaced_columns.employee_data WHERE "Years of Experience" > 3 ORDER BY "Performance Rating" DESC'
    ]
    
    for i, query in enumerate(commands, 1):
        print(f"\n📋 Test {i}: {query}")
        print("-" * 60)
        
        try:
            # Run the query
            result = subprocess.run([
                'uv', 'run', 'python', '-m', 'excel_processor', 
                '--db', 'sample_data', 
                '--query', query
            ], capture_output=True, text=True, env={'PATH': f"{subprocess.os.environ.get('HOME')}/.local/bin:{subprocess.os.environ.get('PATH', '')}"})
            
            if result.returncode == 0:
                print("✅ SUCCESS")
                print(result.stdout)
            else:
                print("❌ FAILED")
                print(f"Error: {result.stderr}")
                
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    test_quoted_columns_and_aliases()