"""SQL parser for Oracle-like syntax with Excel file.sheet notation."""

import re
from typing import List, Optional, Union, Dict, Tuple

from .sql_ast import (
    SQLQuery, SelectNode, FromNode, WhereNode, JoinNode, OrderByNode, 
    LimitNode, GroupByNode, HavingNode, AggregateFunctionNode
)
from .models import (
    TableReference, ColumnReference, Condition, JoinClause, 
    WhereClause, OrderByClause
)
from .exceptions import SQLSyntaxError


class SQLParser:
    """Parser for Oracle-like SQL syntax with Excel file.sheet notation."""
    
    def __init__(self):
        self.aggregate_functions = {
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'STDDEV', 'VARIANCE'
        }
        self.join_types = {
            'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER', 'CROSS'
        }
        self.comparison_operators = {
            '=', '!=', '<>', '<', '>', '<=', '>=', 'LIKE', 'IN', 'NOT IN',
            'IS', 'IS NOT', 'BETWEEN', 'NOT BETWEEN'
        }
        self.logical_operators = {'AND', 'OR', 'NOT'}
    
    def parse(self, query: str) -> SQLQuery:
        """Parse a SQL query string into SQLQuery AST.
        
        Args:
            query: SQL query string
            
        Returns:
            SQLQuery AST object
            
        Raises:
            SQLSyntaxError: If query syntax is invalid
        """
        try:
            # Check for CSV redirection first
            output_file = None
            if '>' in query:
                parts = query.rsplit('>', 1)
                if len(parts) == 2:
                    # Check if this is actually a redirection (not a comparison operator)
                    potential_file = parts[1].strip()
                    left_part = parts[0].strip()
                    
                    # It's a redirection if:
                    # 1. The potential file doesn't start with a digit or operator
                    # 2. The left part doesn't end with a comparison context
                    # 3. The potential file looks like a filename (has extension or no spaces)
                    if (potential_file and 
                        not potential_file[0].isdigit() and
                        not potential_file.startswith(('=', '<', '!')) and
                        ('.' in potential_file or ' ' not in potential_file) and
                        not left_part.endswith(('WHERE', 'AND', 'OR'))):
                        query = parts[0].strip()
                        output_file = potential_file
            
            # Normalize whitespace
            query = re.sub(r'\s+', ' ', query.strip())
            
            if not query:
                raise SQLSyntaxError(query, "Empty or invalid query")
            
            if not query.upper().startswith('SELECT'):
                raise SQLSyntaxError(query, "Only SELECT statements are supported")
            
            # Create SQLQuery object
            sql_query = SQLQuery()
            sql_query.output_file = output_file
            
            # Parse different clauses using regex
            self._parse_query_regex(query, sql_query)
            
            return sql_query
        
        except SQLSyntaxError:
            raise
        except Exception as e:
            raise SQLSyntaxError(query, f"Failed to parse query: {str(e)}")
    
    def _parse_query_regex(self, query: str, sql_query: SQLQuery):
        """Parse SQL query using regex patterns."""

        query_upper = query.upper()
        
        # Parse SELECT clause
        select_match = re.match(r'SELECT\s+(DISTINCT\s+)?(.*?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
        if not select_match:
            if 'FROM' not in query.upper():
                raise SQLSyntaxError(query, "Missing FROM clause - query must specify table(s)")
            else:
                raise SQLSyntaxError(query, "Invalid SELECT clause")
        
        distinct = select_match.group(1) is not None
        columns_str = select_match.group(2).strip()
        columns = self._parse_select_columns(columns_str)
        sql_query.select_node = SelectNode(columns, distinct)
        
        # Parse FROM clause
        from_match = re.search(r'FROM\s+(.*?)(?:\s+WHERE|\s+ORDER\s+BY|\s*$)', query, re.IGNORECASE | re.DOTALL)
        if not from_match:
            raise SQLSyntaxError(query, "Missing FROM clause")
        
        tables_str = from_match.group(1).strip()
        tables = self._parse_from_tables(tables_str)
        sql_query.from_node = FromNode(tables)
        
        # Parse WHERE clause
        where_match = re.search(r'WHERE\s+(.*?)(?:\s+ORDER\s+BY|\s*$)', query, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_str = where_match.group(1).strip()

            where_clause = self._parse_where_conditions(where_str)
            sql_query.where_node = WhereNode(where_clause)
        
        # Parse ORDER BY clause
        order_match = re.search(r'ORDER\s+BY\s+(.*?)$', query, re.IGNORECASE | re.DOTALL)
        if order_match:
            order_str = order_match.group(1).strip()
            order_clause = self._parse_order_by_columns(order_str)
            sql_query.order_by_node = OrderByNode(order_clause)
    
    def _parse_select_columns(self, columns_str: str) -> List[Union[str, ColumnReference, AggregateFunctionNode]]:
        """Parse SELECT column list."""
        if columns_str.strip() == '*':
            return ['*']
        
        columns = []
        # Split by comma, but respect parentheses
        parts = self._split_by_comma(columns_str)
        
        for part in parts:
            part = part.strip()
            if part:
                columns.append(self._parse_column_expression(part))
        
        return columns
    
    def _parse_from_tables(self, tables_str: str) -> List[TableReference]:
        """Parse FROM table list."""
        tables = []
        # Split by comma for multiple tables
        parts = self._split_by_comma(tables_str)
        
        for part in parts:
            part = part.strip()
            if part:
                tables.append(self._parse_table_reference(part))
        
        return tables
    
    def _parse_where_conditions(self, where_str: str) -> WhereClause:
        """Parse WHERE clause conditions."""
        conditions = []
        logical_ops = []
        
        # Split by AND/OR while respecting parentheses
        parts = self._split_by_logical_operators(where_str)
        for i, part in enumerate(parts):
            if part.upper() in ('AND', 'OR'):
                logical_ops.append(part.upper())
            else:
                part = part.strip()
                if part:
                    conditions.append(self._parse_condition(part))
        
        return WhereClause(conditions, logical_ops)
    
    def _parse_order_by_columns(self, order_str: str) -> OrderByClause:
        """Parse ORDER BY column list."""
        columns = []
        directions = []
        
        parts = self._split_by_comma(order_str)
        
        for part in parts:
            part = part.strip()
            if part:
                col_parts = part.split()
                columns.append(col_parts[0])
                if len(col_parts) > 1 and col_parts[-1].upper() in ('ASC', 'DESC'):
                    directions.append(col_parts[-1].upper())
                else:
                    directions.append('ASC')
        
        return OrderByClause(columns, directions)
    
    def _split_by_comma(self, text: str) -> List[str]:
        """Split text by comma, respecting parentheses."""
        parts = []
        current = ""
        paren_depth = 0
        
        for char in text:
            if char == '(':
                paren_depth += 1
                current += char
            elif char == ')':
                paren_depth -= 1
                current += char
            elif char == ',' and paren_depth == 0:
                parts.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            parts.append(current.strip())
        
        return parts
    
    def _split_by_logical_operators(self, text: str) -> List[str]:
        """Split text by AND/OR operators, respecting parentheses."""
        parts = []
        current = ""
        paren_depth = 0
        i = 0
        
        while i < len(text):
            char = text[i]
            
            if char == '(':
                paren_depth += 1
                current += char
                i += 1
            elif char == ')':
                paren_depth -= 1
                current += char
                i += 1
            elif paren_depth == 0:
                # Check for AND/OR with word boundaries
                if (text[i:i+3].upper() == 'AND' and 
                    (i == 0 or not text[i-1].isalnum()) and 
                    (i+3 >= len(text) or not text[i+3].isalnum())):
                    if current.strip():
                        parts.append(current.strip())
                    parts.append('AND')
                    current = ""
                    i += 3
                elif (text[i:i+2].upper() == 'OR' and 
                      (i == 0 or not text[i-1].isalnum()) and 
                      (i+2 >= len(text) or not text[i+2].isalnum())):
                    if current.strip():
                        parts.append(current.strip())
                    parts.append('OR')
                    current = ""
                    i += 2
                else:
                    current += char
                    i += 1
            else:
                current += char
                i += 1
        
        if current.strip():
            parts.append(current.strip())
        
        return parts


    
    def _parse_column_expression(self, expr: str) -> Union[str, ColumnReference, AggregateFunctionNode]:
        """Parse a column expression (could be column name, *, or function)."""
        expr = expr.strip()
        
        if expr == '*':
            return '*'
        
        # Check for aggregate functions
        func_match = re.match(r'(\w+)\s*\(\s*(.*?)\s*\)', expr, re.IGNORECASE)
        if func_match:
            func_name = func_match.group(1).upper()
            func_args = func_match.group(2).strip()
            
            if func_name in self.aggregate_functions:
                distinct = False
                if func_args.upper().startswith('DISTINCT '):
                    distinct = True
                    func_args = func_args[9:].strip()  # Remove 'DISTINCT '
                
                return AggregateFunctionNode(func_name, func_args, distinct)
        
        # Check for table.column notation
        if '.' in expr:
            parts = expr.split('.')
            if len(parts) == 2:
                return ColumnReference(parts[1], parts[0])
        
        return expr
    

    
    def _parse_table_reference(self, table_expr: str) -> TableReference:
        """Parse table reference in format 'file.sheet' or 'file.sheet AS alias'."""
        parts = table_expr.split()
        
        # Handle alias
        alias = None
        if len(parts) >= 3 and parts[-2].upper() == 'AS':
            alias = parts[-1]
            table_name = ' '.join(parts[:-2])
        elif len(parts) == 2:
            # Could be "table alias" without AS keyword
            if '.' in parts[0]:
                table_name = parts[0]
                alias = parts[1]
            else:
                table_name = table_expr
        else:
            table_name = parts[0] if parts else table_expr
        
        # Parse file.sheet notation
        if '.' not in table_name:
            raise SQLSyntaxError(
                table_expr, 
                f"Table reference '{table_name}' must be in format 'file.sheet'",
                suggestion="Use format like 'employees.xlsx.sheet1' or 'data.employees'"
            )
        
        # Split on last dot to handle files with dots in names
        file_part, sheet_name = table_name.rsplit('.', 1)
        
        return TableReference(file_part, sheet_name, alias)
    

    
    def _parse_condition(self, condition_str: str) -> Condition:
        """Parse a single condition like 'column = value' or 'ROWNUM <= 100'."""
        condition_str = condition_str.strip()
        
        # Handle ROWNUM specially
        if condition_str.upper().startswith('ROWNUM'):
            match = re.match(r'ROWNUM\s*([<>=!]+)\s*(.+)', condition_str, re.IGNORECASE)
            if match:
                operator = match.group(1)
                value = match.group(2).strip()
                try:
                    value = int(value)
                except ValueError:
                    pass
                return Condition('ROWNUM', operator, value)
        
        # Find operator
        for op in sorted(self.comparison_operators, key=len, reverse=True):
            if op in condition_str.upper():
                # Find the actual position in original case
                op_pos = condition_str.upper().find(op)
                if op_pos >= 0:  # Changed from > 0 to >= 0
                    left = condition_str[:op_pos].strip()
                    right = condition_str[op_pos + len(op):].strip()
                    
                    # Make sure we have both left and right parts
                    if left and right:
                        # Parse right side value
                        if right.startswith("'") and right.endswith("'"):
                            right = right[1:-1]  # Remove quotes
                        elif right.isdigit():
                            right = int(right)
                        elif re.match(r'^\d+\.\d+$', right):
                            right = float(right)
                        
                        return Condition(left, op, right)
        
        raise SQLSyntaxError(condition_str, f"Invalid condition: {condition_str}")
    

    

    
    def validate_syntax(self, query: str) -> List[str]:
        """Validate SQL syntax and return list of errors.
        
        Args:
            query: SQL query string
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        try:
            self.parse(query)
        except SQLSyntaxError as e:
            errors.append(e.message)
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
        
        return errors
    
    def suggest_correction(self, query: str, error_position: Optional[int] = None) -> Optional[str]:
        """Suggest corrections for common SQL syntax errors.
        
        Args:
            query: Original query with error
            error_position: Position of error in query
            
        Returns:
            Suggested correction or None
        """
        query_upper = query.upper()
        
        # Common corrections
        if 'SELECT' not in query_upper:
            return "Query must start with SELECT"
        
        if 'FROM' not in query_upper:
            return "Query must include FROM clause"
        
        if query.count('.') == 0 and 'FROM' in query_upper:
            return "Table references must be in format 'file.sheet'"
        
        if query.count('(') != query.count(')'):
            return "Mismatched parentheses"
        
        return None