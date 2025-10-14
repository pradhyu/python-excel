"""SQL parser for Oracle-like syntax with Excel file.sheet notation."""

import re
from typing import List, Optional, Union, Dict, Tuple

from .sql_ast import (
    SQLQuery, SelectNode, FromNode, WhereNode, JoinNode, OrderByNode, 
    LimitNode, GroupByNode, HavingNode, AggregateFunctionNode, CreateTableAsNode, 
    WindowFunctionNode, ColumnAliasNode, LiteralNode
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
        self.window_functions = {
            'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'NTILE', 
            'LAG', 'LEAD', 'FIRST_VALUE', 'LAST_VALUE'
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
            
            query_upper = query.upper()
            if not (query_upper.startswith('SELECT') or query_upper.startswith('CREATE TABLE')):
                raise SQLSyntaxError(query, "Only SELECT and CREATE TABLE AS statements are supported")
            
            # Create SQLQuery object
            sql_query = SQLQuery()
            sql_query.output_file = output_file
            
            # Check if this is a CREATE TABLE AS statement
            if query_upper.startswith('CREATE TABLE'):
                self._parse_create_table_as(query, sql_query)
            else:
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
        from_match = re.search(r'FROM\s+(.*?)(?:\s+WHERE|\s+GROUP\s+BY|\s+ORDER\s+BY|\s*$)', query, re.IGNORECASE | re.DOTALL)
        if not from_match:
            raise SQLSyntaxError(query, "Missing FROM clause")
        
        tables_str = from_match.group(1).strip()
        tables = self._parse_from_tables(tables_str)
        sql_query.from_node = FromNode(tables)
        
        # Parse WHERE clause
        where_match = re.search(r'WHERE\s+(.*?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s*$)', query, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_str = where_match.group(1).strip()
            where_clause = self._parse_where_conditions(where_str)
            sql_query.where_node = WhereNode(where_clause)
        
        # Parse GROUP BY clause
        group_match = re.search(r'GROUP\s+BY\s+(.*?)(?:\s+HAVING|\s+ORDER\s+BY|\s*$)', query, re.IGNORECASE | re.DOTALL)
        if group_match:
            group_str = group_match.group(1).strip()
            group_columns = self._parse_group_by_columns(group_str)
            sql_query.group_by_node = GroupByNode(group_columns)
        
        # Parse HAVING clause
        having_match = re.search(r'HAVING\s+(.*?)(?:\s+ORDER\s+BY|\s*$)', query, re.IGNORECASE | re.DOTALL)
        if having_match:
            having_str = having_match.group(1).strip()
            having_clause = self._parse_where_conditions(having_str)  # Same logic as WHERE
            sql_query.having_node = HavingNode(having_clause)
        
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
    
    def _parse_column_expression(self, expr: str) -> Union[str, ColumnReference, AggregateFunctionNode, WindowFunctionNode]:
        """Parse a column expression (could be column name, *, function, or window function)."""
        expr = expr.strip()
        if expr == '*':
            return '*'
        
        # Check for column alias (... AS alias)
        alias = None
        alias_match = re.search(r'\s+AS\s+(\w+)$', expr, re.IGNORECASE)
        if alias_match:
            alias = alias_match.group(1)
            expr = expr[:alias_match.start()].strip()
        
        # Check for window functions (function(...) OVER (...))
        window_match = re.match(r'(\w+)\s*\(\s*(.*?)\s*\)\s+OVER\s*\(\s*(.*?)\s*\)', expr, re.IGNORECASE | re.DOTALL)
        if window_match:
            func_name = window_match.group(1).upper()
            func_args = window_match.group(2).strip()
            over_clause = window_match.group(3).strip()
            if func_name in self.window_functions:
                window_func = self._parse_window_function(func_name, func_args, over_clause)
                if alias:
                    window_func.alias = alias
                return window_func
        
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
                agg_func = AggregateFunctionNode(func_name, func_args, distinct)
                if alias:
                    agg_func.alias = alias
                return agg_func
        
        # Parse quoted column names and regular column references
        return self._parse_column_reference(expr, alias)
    
    def _parse_column_reference(self, expr: str, alias: str = None) -> Union[str, ColumnReference]:
        """Parse a column reference, handling quoted names and table qualifiers."""
        # Handle quoted column names (single or double quotes)
        if ((expr.startswith('"') and expr.endswith('"')) or 
            (expr.startswith("'") and expr.endswith("'"))):
            # Remove quotes
            column_name = expr[1:-1]
            return ColumnReference(column_name, alias=alias)
        
        # Check for table.column notation
        if '.' in expr:
            # Handle quoted table or column names in table.column format
            parts = expr.split('.')
            if len(parts) == 2:
                table_part = parts[0].strip()
                column_part = parts[1].strip()
                
                # Remove quotes from table name if present
                if ((table_part.startswith('"') and table_part.endswith('"')) or 
                    (table_part.startswith("'") and table_part.endswith("'"))):
                    table_part = table_part[1:-1]
                
                # Remove quotes from column name if present
                if ((column_part.startswith('"') and column_part.endswith('"')) or 
                    (column_part.startswith("'") and column_part.endswith("'"))):
                    column_part = column_part[1:-1]
                
                return ColumnReference(column_part, table_part, alias)
        
        # Regular column name (possibly with alias)
        if alias:
            return ColumnReference(expr, alias=alias)
        return expr
    
    def _parse_window_function(self, func_name: str, func_args: str, over_clause: str) -> WindowFunctionNode:
        """Parse a window function with OVER clause."""
        # Parse PARTITION BY and ORDER BY from OVER clause
        partition_by = []
        order_by = []
        order_directions = []
        
        # Parse PARTITION BY
        partition_match = re.search(r'PARTITION\s+BY\s+(.*?)(?:\s+ORDER\s+BY|$)', over_clause, re.IGNORECASE)
        if partition_match:
            partition_str = partition_match.group(1).strip()
            partition_by = [col.strip() for col in partition_str.split(',')]
        
        # Parse ORDER BY
        order_match = re.search(r'ORDER\s+BY\s+(.*?)$', over_clause, re.IGNORECASE)
        if order_match:
            order_str = order_match.group(1).strip()
            order_parts = [part.strip() for part in order_str.split(',')]
            for part in order_parts:
                part_tokens = part.split()
                order_by.append(part_tokens[0])
                if len(part_tokens) > 1 and part_tokens[-1].upper() in ('ASC', 'DESC'):
                    order_directions.append(part_tokens[-1].upper())
                else:
                    order_directions.append('ASC')
        
        return WindowFunctionNode(func_name, func_args or None, partition_by, order_by, order_directions)
    
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
    
    def _parse_group_by_columns(self, group_str: str) -> List[str]:
        """Parse GROUP BY column list."""
        columns = []
        parts = self._split_by_comma(group_str)
        
        for part in parts:
            part = part.strip()
            if part:
                columns.append(part)
        
        return columns
    
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


    
    def _parse_column_expression(self, expr: str) -> Union[str, ColumnReference, AggregateFunctionNode, WindowFunctionNode, ColumnAliasNode, LiteralNode]:
        """Parse a column expression (could be column name, *, function, window function, or alias)."""
        expr = expr.strip()
        
        if expr == '*':
            return '*'
        
        # Check for column alias (expression AS alias)
        alias_match = re.match(r'(.*?)\s+AS\s+(["\']?)(\w+|[^"\']+)\2\s*$', expr, re.IGNORECASE)
        if alias_match:
            expression_part = alias_match.group(1).strip()
            alias = alias_match.group(3).strip()
            
            # Parse the expression part recursively
            parsed_expression = self._parse_single_column_expression(expression_part)
            return ColumnAliasNode(parsed_expression, alias)
        
        # No alias, parse as single expression
        return self._parse_single_column_expression(expr)
    
    def _parse_single_column_expression(self, expr: str) -> Union[str, ColumnReference, AggregateFunctionNode, WindowFunctionNode, LiteralNode]:
        """Parse a single column expression without alias."""
        expr = expr.strip()
        
        # Check for numeric literals
        if re.match(r'^\d+(\.\d+)?$', expr):
            return LiteralNode(expr, 'number')
        
        # Check for window functions (function(...) OVER (...))
        window_match = re.match(r'(\w+)\s*\(\s*(.*?)\s*\)\s+OVER\s*\(\s*(.*?)\s*\)', expr, re.IGNORECASE | re.DOTALL)
        if window_match:
            func_name = window_match.group(1).upper()
            func_args = window_match.group(2).strip()
            over_clause = window_match.group(3).strip()
            
            if func_name in self.window_functions:
                return self._parse_window_function(func_name, func_args, over_clause)
        
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
        
        # Check for quoted column names (with spaces) - treat as column references, not literals
        if ((expr.startswith('"') and expr.endswith('"')) or 
            (expr.startswith("'") and expr.endswith("'"))):
            column_name = expr[1:-1]  # Remove quotes
            return ColumnReference(column_name)
        
        # Check for table.column notation
        if '.' in expr:
            parts = expr.split('.')
            if len(parts) == 2:
                table_part = parts[0].strip()
                column_part = parts[1].strip()
                
                # Handle quoted table or column names
                if ((table_part.startswith('"') and table_part.endswith('"')) or 
                    (table_part.startswith("'") and table_part.endswith("'"))):
                    table_part = table_part[1:-1]
                
                if ((column_part.startswith('"') and column_part.endswith('"')) or 
                    (column_part.startswith("'") and column_part.endswith("'"))):
                    column_part = column_part[1:-1]
                
                return ColumnReference(column_part, table_part)
        
        return expr
    

    
    def _parse_table_reference(self, table_expr: str) -> TableReference:
        """Parse table reference in format 'file.sheet' or 'file.sheet AS alias', or temporary table name.
        
        Supports quoted file and sheet names: "Employee Data"."Staff Info"
        """
        table_expr = table_expr.strip()
        
        # Handle alias - look for AS keyword, but be careful with quoted names
        alias = None
        table_name = table_expr
        
        # Check for AS keyword (case insensitive)
        as_match = re.search(r'\s+AS\s+(\w+)$', table_expr, re.IGNORECASE)
        if as_match:
            alias = as_match.group(1)
            table_name = table_expr[:as_match.start()].strip()
        else:
            # Check for alias without AS keyword - but only if we don't have quoted names
            parts = table_expr.split()
            if len(parts) == 2 and not ('"' in table_expr or "'" in table_expr):
                # Simple case: table_name alias (no quotes)
                if '.' in parts[0]:
                    table_name = parts[0]
                    alias = parts[1]
        
        # Now parse the table name (which might be quoted)
        if '.' not in table_name:
            # Simple table name (could be temporary table)
            # Remove quotes if present
            if ((table_name.startswith('"') and table_name.endswith('"')) or 
                (table_name.startswith("'") and table_name.endswith("'"))):
                table_name = table_name[1:-1]
            return TableReference(table_name, "", alias)
        
        # Parse file.sheet format with potential quotes
        # We need to be smart about splitting on dots when quotes are involved
        file_part, sheet_part = self._split_table_name(table_name)
        
        # Remove quotes from file and sheet names if present
        if ((file_part.startswith('"') and file_part.endswith('"')) or 
            (file_part.startswith("'") and file_part.endswith("'"))):
            file_part = file_part[1:-1]
        
        if ((sheet_part.startswith('"') and sheet_part.endswith('"')) or 
            (sheet_part.startswith("'") and sheet_part.endswith("'"))):
            sheet_part = sheet_part[1:-1]
        
        return TableReference(file_part, sheet_part, alias)
    
    def _split_table_name(self, table_name: str) -> tuple:
        """Split table name into file and sheet parts, handling quoted names.
        
        Examples:
        - 'file.sheet' -> ('file', 'sheet')
        - '"Employee Data"."Staff Info"' -> ('"Employee Data"', '"Staff Info"')
        - 'file."Sheet Name"' -> ('file', '"Sheet Name"')
        """
        # If no quotes, use simple split
        if '"' not in table_name and "'" not in table_name:
            return table_name.rsplit('.', 1)
        
        # Handle quoted names - we need to find the dot that's not inside quotes
        in_quotes = False
        quote_char = None
        dot_positions = []
        
        for i, char in enumerate(table_name):
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char == '.' and not in_quotes:
                dot_positions.append(i)
        
        if not dot_positions:
            # No unquoted dots found - treat as simple name
            return (table_name, "")
        
        # Use the last unquoted dot to split
        last_dot = dot_positions[-1]
        file_part = table_name[:last_dot]
        sheet_part = table_name[last_dot + 1:]
        
        return (file_part, sheet_part)
    

    
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
        
        # Find operator with proper word boundaries
        for op in sorted(self.comparison_operators, key=len, reverse=True):
            # For word operators like IN, LIKE, etc., use word boundaries
            if op.isalpha() or ' ' in op:
                pattern = r'\b' + re.escape(op) + r'\b'
                match = re.search(pattern, condition_str, re.IGNORECASE)
                if match:
                    op_pos = match.start()
                    left = condition_str[:op_pos].strip()
                    right = condition_str[match.end():].strip()
                    
                    # Make sure we have both left and right parts
                    if left and right:
                        # Parse right side value - handle NULL specially
                        if right.upper() == 'NULL':
                            right = 'NULL'
                        elif ((right.startswith("'") and right.endswith("'")) or 
                            (right.startswith('"') and right.endswith('"'))):
                            right = right[1:-1]  # Remove quotes
                        elif right.isdigit():
                            right = int(right)
                        elif re.match(r'^\d+\.\d+$', right):
                            right = float(right)
                        
                        return Condition(left, op, right)
            else:
                # For symbol operators like =, !=, etc., use simple search
                if op in condition_str:
                    op_pos = condition_str.find(op)
                    if op_pos >= 0:
                        left = condition_str[:op_pos].strip()
                        right = condition_str[op_pos + len(op):].strip()
                        
                        # Make sure we have both left and right parts
                        if left and right:
                            # Parse right side value
                            if ((right.startswith("'") and right.endswith("'")) or 
                                (right.startswith('"') and right.endswith('"'))):
                                right = right[1:-1]  # Remove quotes
                            elif right.isdigit():
                                right = int(right)
                            elif re.match(r'^\d+\.\d+$', right):
                                right = float(right)
                            
                            return Condition(left, op, right)
        
        raise SQLSyntaxError(condition_str, f"Invalid condition: {condition_str}")
    
    def _parse_window_function(self, func_name: str, func_args: str, over_clause: str) -> WindowFunctionNode:
        """Parse a window function with OVER clause."""
        # Parse function arguments
        column = func_args if func_args else None
        
        # Parse OVER clause
        partition_by = []
        order_by = []
        order_directions = []
        
        if over_clause:
            # Parse PARTITION BY
            partition_match = re.search(r'PARTITION\s+BY\s+(.*?)(?:\s+ORDER\s+BY|$)', over_clause, re.IGNORECASE)
            if partition_match:
                partition_str = partition_match.group(1).strip()
                partition_by = [col.strip() for col in partition_str.split(',')]
            
            # Parse ORDER BY
            order_match = re.search(r'ORDER\s+BY\s+(.*?)$', over_clause, re.IGNORECASE)
            if order_match:
                order_str = order_match.group(1).strip()
                order_parts = [part.strip() for part in order_str.split(',')]
                
                for part in order_parts:
                    part_tokens = part.split()
                    if len(part_tokens) >= 2 and part_tokens[-1].upper() in ('ASC', 'DESC'):
                        order_by.append(' '.join(part_tokens[:-1]))
                        order_directions.append(part_tokens[-1].upper())
                    else:
                        order_by.append(part)
                        order_directions.append('ASC')
        
        return WindowFunctionNode(func_name, column, partition_by, order_by, order_directions)
    
    def _parse_create_table_as(self, query: str, sql_query: SQLQuery):
        """Parse CREATE TABLE AS statement."""
        # Pattern: CREATE TABLE table_name AS (SELECT ...)
        # or: CREATE TABLE table_name AS SELECT ...
        
        pattern = r'CREATE\s+TABLE\s+(\w+)\s+AS\s*\(?(.*?)\)?$'
        match = re.match(pattern, query, re.IGNORECASE | re.DOTALL)
        
        if not match:
            raise SQLSyntaxError(query, "Invalid CREATE TABLE AS syntax. Expected: CREATE TABLE table_name AS SELECT ...")
        
        table_name = match.group(1)
        select_query_str = match.group(2).strip()
        
        # Parse the SELECT query
        select_query = SQLQuery()
        self._parse_query_regex(select_query_str, select_query)
        
        # Create the CREATE TABLE AS node
        sql_query.query_type = "CREATE_TABLE_AS"
        sql_query.create_table_as_node = CreateTableAsNode(table_name, select_query)
    
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