"""Unit tests for SQL parser functionality."""

import pytest
from excel_processor.sql_parser import SQLParser
from excel_processor.sql_ast import SQLQuery, SelectNode, FromNode, WhereNode, OrderByNode
from excel_processor.models import TableReference, ColumnReference, Condition
from excel_processor.exceptions import SQLSyntaxError


class TestSQLParser:
    """Test cases for SQLParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = SQLParser()
    
    def test_simple_select_all(self):
        """Test simple SELECT * query."""
        query = "SELECT * FROM employees.xlsx.sheet1"
        result = self.parser.parse(query)
        
        assert isinstance(result, SQLQuery)
        assert result.select_node is not None
        assert result.select_node.is_wildcard is True
        assert result.from_node is not None
        assert len(result.from_node.tables) == 1
        assert result.from_node.tables[0].file_name == "employees.xlsx"
        assert result.from_node.tables[0].sheet_name == "sheet1"
    
    def test_select_specific_columns(self):
        """Test SELECT with specific columns."""
        query = "SELECT id, name, age FROM employees.xlsx.sheet1"
        result = self.parser.parse(query)
        
        assert result.select_node is not None
        assert len(result.select_node.columns) == 3
        assert "id" in result.select_node.columns
        assert "name" in result.select_node.columns
        assert "age" in result.select_node.columns
    
    def test_select_distinct(self):
        """Test SELECT DISTINCT."""
        query = "SELECT DISTINCT department FROM employees.xlsx.sheet1"
        result = self.parser.parse(query)
        
        assert result.select_node is not None
        assert result.select_node.distinct is True
        assert len(result.select_node.columns) == 1
        assert "department" in result.select_node.columns
    
    def test_table_reference_parsing(self):
        """Test parsing table references in file.sheet format."""
        query = "SELECT * FROM data.xlsx.employees"
        result = self.parser.parse(query)
        
        table_ref = result.from_node.tables[0]
        assert table_ref.file_name == "data.xlsx"
        assert table_ref.sheet_name == "employees"
        assert table_ref.alias is None
    
    def test_table_reference_with_alias(self):
        """Test table reference with alias."""
        query = "SELECT * FROM employees.xlsx.sheet1 AS e"
        result = self.parser.parse(query)
        
        table_ref = result.from_node.tables[0]
        assert table_ref.file_name == "employees.xlsx"
        assert table_ref.sheet_name == "sheet1"
        assert table_ref.alias == "e"
    
    def test_table_reference_without_as_keyword(self):
        """Test table reference with alias without AS keyword."""
        query = "SELECT * FROM employees.xlsx.sheet1 e"
        result = self.parser.parse(query)
        
        table_ref = result.from_node.tables[0]
        assert table_ref.file_name == "employees.xlsx"
        assert table_ref.sheet_name == "sheet1"
        assert table_ref.alias == "e"
    
    def test_multiple_tables_in_from(self):
        """Test multiple tables in FROM clause (implicit join)."""
        query = "SELECT * FROM employees.xlsx.sheet1, orders.xlsx.sheet1"
        result = self.parser.parse(query)
        
        assert len(result.from_node.tables) == 2
        assert result.from_node.tables[0].file_name == "employees.xlsx"
        assert result.from_node.tables[1].file_name == "orders.xlsx"
    
    def test_where_clause_simple(self):
        """Test simple WHERE clause."""
        query = "SELECT * FROM employees.xlsx.sheet1 WHERE age > 25"
        result = self.parser.parse(query)
        
        assert result.where_node is not None
        assert len(result.where_node.where_clause.conditions) == 1
        
        condition = result.where_node.where_clause.conditions[0]
        assert condition.left == "age"
        assert condition.operator == ">"
        assert condition.right == 25
    
    def test_where_clause_string_value(self):
        """Test WHERE clause with string value."""
        query = "SELECT * FROM employees.xlsx.sheet1 WHERE name = 'John'"
        result = self.parser.parse(query)
        
        condition = result.where_node.where_clause.conditions[0]
        assert condition.left == "name"
        assert condition.operator == "="
        assert condition.right == "John"
    
    def test_where_clause_multiple_conditions(self):
        """Test WHERE clause with multiple conditions."""
        query = "SELECT * FROM employees.xlsx.sheet1 WHERE age > 25 AND department = 'IT'"
        result = self.parser.parse(query)
        
        assert len(result.where_node.where_clause.conditions) == 2
        assert len(result.where_node.where_clause.logical_operators) == 1
        assert result.where_node.where_clause.logical_operators[0] == "AND"
        
        # Check first condition
        condition1 = result.where_node.where_clause.conditions[0]
        assert condition1.left == "age"
        assert condition1.operator == ">"
        assert condition1.right == 25
        
        # Check second condition
        condition2 = result.where_node.where_clause.conditions[1]
        assert condition2.left == "department"
        assert condition2.operator == "="
        assert condition2.right == "IT"
    
    def test_rownum_condition(self):
        """Test ROWNUM condition for limiting results."""
        query = "SELECT * FROM employees.xlsx.sheet1 WHERE ROWNUM <= 100"
        result = self.parser.parse(query)
        
        condition = result.where_node.where_clause.conditions[0]
        assert condition.left == "ROWNUM"
        assert condition.operator == "<="
        assert condition.right == 100
    
    def test_order_by_clause(self):
        """Test ORDER BY clause."""
        query = "SELECT * FROM employees.xlsx.sheet1 ORDER BY age DESC"
        result = self.parser.parse(query)
        
        assert result.order_by_node is not None
        order_clause = result.order_by_node.order_by_clause
        assert len(order_clause.columns) == 1
        assert order_clause.columns[0] == "age"
        assert order_clause.directions[0] == "DESC"
    
    def test_order_by_multiple_columns(self):
        """Test ORDER BY with multiple columns."""
        query = "SELECT * FROM employees.xlsx.sheet1 ORDER BY department ASC, age DESC"
        result = self.parser.parse(query)
        
        order_clause = result.order_by_node.order_by_clause
        assert len(order_clause.columns) == 2
        assert order_clause.columns[0] == "department"
        assert order_clause.directions[0] == "ASC"
        assert order_clause.columns[1] == "age"
        assert order_clause.directions[1] == "DESC"
    
    def test_order_by_default_asc(self):
        """Test ORDER BY with default ASC direction."""
        query = "SELECT * FROM employees.xlsx.sheet1 ORDER BY name"
        result = self.parser.parse(query)
        
        order_clause = result.order_by_node.order_by_clause
        assert order_clause.columns[0] == "name"
        assert order_clause.directions[0] == "ASC"
    
    def test_csv_export_redirection(self):
        """Test CSV export redirection with > operator."""
        query = "SELECT * FROM employees.xlsx.sheet1 > output.csv"
        result = self.parser.parse(query)
        
        assert result.output_file == "output.csv"
        assert result.select_node is not None
        assert result.from_node is not None
    
    def test_complex_query(self):
        """Test complex query with multiple clauses."""
        query = """
        SELECT DISTINCT name, age, department 
        FROM employees.xlsx.sheet1 
        WHERE age > 25 AND department = 'IT' 
        ORDER BY age DESC, name ASC
        """
        result = self.parser.parse(query)
        
        # Check SELECT
        assert result.select_node.distinct is True
        assert len(result.select_node.columns) == 3
        
        # Check FROM
        assert len(result.from_node.tables) == 1
        assert result.from_node.tables[0].file_name == "employees.xlsx"
        
        # Check WHERE
        assert len(result.where_node.where_clause.conditions) == 2
        
        # Check ORDER BY
        assert len(result.order_by_node.order_by_clause.columns) == 2
    
    def test_aggregate_functions(self):
        """Test aggregate functions in SELECT."""
        query = "SELECT COUNT(*), AVG(age), MAX(salary) FROM employees.xlsx.sheet1"
        result = self.parser.parse(query)
        
        columns = result.select_node.columns
        assert len(columns) == 3
        
        # Check that aggregate functions are parsed
        # Note: The exact type checking depends on implementation details
        assert any("COUNT" in str(col) for col in columns)
        assert any("AVG" in str(col) for col in columns)
        assert any("MAX" in str(col) for col in columns)
    
    def test_column_with_table_prefix(self):
        """Test column references with table prefix."""
        query = "SELECT e.name, e.age FROM employees.xlsx.sheet1 e"
        result = self.parser.parse(query)
        
        columns = result.select_node.columns
        assert len(columns) == 2
        
        # Check for ColumnReference objects or string representations
        # The exact implementation may vary
        assert any("name" in str(col) for col in columns)
        assert any("age" in str(col) for col in columns)
    
    def test_file_with_dots_in_name(self):
        """Test parsing files with dots in their names."""
        query = "SELECT * FROM file.with.dots.xlsx.sheet1"
        result = self.parser.parse(query)
        
        table_ref = result.from_node.tables[0]
        assert table_ref.file_name == "file.with.dots.xlsx"
        assert table_ref.sheet_name == "sheet1"
    
    def test_invalid_query_no_select(self):
        """Test error handling for query without SELECT."""
        query = "FROM employees.xlsx.sheet1"
        
        with pytest.raises(SQLSyntaxError) as exc_info:
            self.parser.parse(query)
        assert "SELECT" in str(exc_info.value) or "Only SELECT statements" in str(exc_info.value)
    
    def test_invalid_query_no_from(self):
        """Test error handling for query without FROM."""
        query = "SELECT *"
        
        with pytest.raises(SQLSyntaxError) as exc_info:
            self.parser.parse(query)
        assert "FROM" in str(exc_info.value) or "must specify" in str(exc_info.value)
    
    def test_invalid_table_reference(self):
        """Test error handling for invalid table reference."""
        query = "SELECT * FROM invalid_table"
        
        with pytest.raises(SQLSyntaxError) as exc_info:
            self.parser.parse(query)
        assert "file.sheet" in str(exc_info.value)
    
    def test_empty_query(self):
        """Test error handling for empty query."""
        query = ""
        
        with pytest.raises(SQLSyntaxError) as exc_info:
            self.parser.parse(query)
        assert "Empty" in str(exc_info.value) or "invalid" in str(exc_info.value)
    
    def test_validate_syntax_valid_query(self):
        """Test syntax validation for valid query."""
        query = "SELECT * FROM employees.xlsx.sheet1"
        errors = self.parser.validate_syntax(query)
        assert len(errors) == 0
    
    def test_validate_syntax_invalid_query(self):
        """Test syntax validation for invalid query."""
        query = "SELECT * FROM invalid_table"
        errors = self.parser.validate_syntax(query)
        assert len(errors) > 0
        assert any("file.sheet" in error for error in errors)
    
    def test_suggest_correction_no_select(self):
        """Test correction suggestion for missing SELECT."""
        query = "FROM employees.xlsx.sheet1"
        suggestion = self.parser.suggest_correction(query)
        assert suggestion is not None
        assert "SELECT" in suggestion
    
    def test_suggest_correction_no_from(self):
        """Test correction suggestion for missing FROM."""
        query = "SELECT *"
        suggestion = self.parser.suggest_correction(query)
        assert suggestion is not None
        assert "FROM" in suggestion
    
    def test_suggest_correction_invalid_table_format(self):
        """Test correction suggestion for invalid table format."""
        query = "SELECT * FROM invalid_table"
        suggestion = self.parser.suggest_correction(query)
        assert suggestion is not None
        assert "file.sheet" in suggestion
    
    def test_suggest_correction_mismatched_parentheses(self):
        """Test correction suggestion for mismatched parentheses."""
        query = "SELECT COUNT( FROM employees.xlsx.sheet1"
        suggestion = self.parser.suggest_correction(query)
        assert suggestion is not None
        assert "parentheses" in suggestion
    
    def test_case_insensitive_keywords(self):
        """Test that SQL keywords are case insensitive."""
        query = "select * from employees.xlsx.sheet1 where age > 25 order by name"
        result = self.parser.parse(query)
        
        assert result.select_node is not None
        assert result.from_node is not None
        assert result.where_node is not None
        assert result.order_by_node is not None
    
    def test_whitespace_handling(self):
        """Test handling of various whitespace patterns."""
        query = """
        SELECT   *   
        FROM     employees.xlsx.sheet1   
        WHERE    age > 25    
        ORDER BY name
        """
        result = self.parser.parse(query)
        
        assert result.select_node is not None
        assert result.from_node is not None
        assert result.where_node is not None
        assert result.order_by_node is not None
    
    def test_comparison_operators(self):
        """Test various comparison operators."""
        operators_and_values = [
            ("=", "'test'", "test"),
            ("!=", "5", 5),
            ("<>", "10", 10),
            ("<", "100", 100),
            (">", "50", 50),
            ("<=", "75", 75),
            (">=", "25", 25)
        ]
        
        for op, value_str, expected_value in operators_and_values:
            query = f"SELECT * FROM employees.xlsx.sheet1 WHERE age {op} {value_str}"
            result = self.parser.parse(query)
            
            condition = result.where_node.where_clause.conditions[0]
            assert condition.operator == op
            assert condition.right == expected_value
    
    def test_numeric_value_parsing(self):
        """Test parsing of numeric values in conditions."""
        # Integer
        query = "SELECT * FROM employees.xlsx.sheet1 WHERE age = 25"
        result = self.parser.parse(query)
        condition = result.where_node.where_clause.conditions[0]
        assert condition.right == 25
        assert isinstance(condition.right, int)
        
        # Float
        query = "SELECT * FROM employees.xlsx.sheet1 WHERE salary = 50000.50"
        result = self.parser.parse(query)
        condition = result.where_node.where_clause.conditions[0]
        assert condition.right == 50000.50
        assert isinstance(condition.right, float)
    
    def test_query_reconstruction(self):
        """Test that parsed query can be reconstructed to string."""
        original_query = "SELECT name, age FROM employees.xlsx.sheet1 WHERE age > 25 ORDER BY name"
        result = self.parser.parse(original_query)
        
        # The reconstructed query should contain the main elements
        reconstructed = str(result)
        assert "SELECT" in reconstructed
        assert "FROM" in reconstructed
        assert "WHERE" in reconstructed
        assert "ORDER BY" in reconstructed