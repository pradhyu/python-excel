"""SQL Abstract Syntax Tree nodes for query parsing."""

from abc import ABC, abstractmethod
from typing import List, Optional, Union, Any
from .models import TableReference, ColumnReference, Condition, JoinClause, WhereClause, OrderByClause


class ASTNode(ABC):
    """Base class for all SQL AST nodes."""
    
    @abstractmethod
    def __str__(self) -> str:
        """String representation of the AST node."""
        pass


class SelectNode(ASTNode):
    """Represents a SELECT clause in SQL."""
    
    def __init__(self, columns: List[Union[str, ColumnReference]], distinct: bool = False):
        self.columns = columns
        self.distinct = distinct
        self.is_wildcard = len(columns) == 1 and str(columns[0]) == "*"
    
    def __str__(self) -> str:
        select_part = "SELECT DISTINCT" if self.distinct else "SELECT"
        columns_str = ", ".join(str(col) for col in self.columns)
        return f"{select_part} {columns_str}"


class FromNode(ASTNode):
    """Represents a FROM clause in SQL."""
    
    def __init__(self, tables: List[TableReference]):
        self.tables = tables
    
    def __str__(self) -> str:
        tables_str = ", ".join(str(table) for table in self.tables)
        return f"FROM {tables_str}"


class WhereNode(ASTNode):
    """Represents a WHERE clause in SQL."""
    
    def __init__(self, where_clause: WhereClause):
        self.where_clause = where_clause
    
    def __str__(self) -> str:
        return f"WHERE {self.where_clause}"


class JoinNode(ASTNode):
    """Represents a JOIN clause in SQL."""
    
    def __init__(self, join_clause: JoinClause):
        self.join_clause = join_clause
    
    def __str__(self) -> str:
        return str(self.join_clause)


class OrderByNode(ASTNode):
    """Represents an ORDER BY clause in SQL."""
    
    def __init__(self, order_by_clause: OrderByClause):
        self.order_by_clause = order_by_clause
    
    def __str__(self) -> str:
        return str(self.order_by_clause)


class LimitNode(ASTNode):
    """Represents a LIMIT clause (ROWNUM in Oracle-style)."""
    
    def __init__(self, limit: int, offset: int = 0):
        self.limit = limit
        self.offset = offset
    
    def __str__(self) -> str:
        if self.offset > 0:
            return f"LIMIT {self.limit} OFFSET {self.offset}"
        return f"LIMIT {self.limit}"


class GroupByNode(ASTNode):
    """Represents a GROUP BY clause in SQL."""
    
    def __init__(self, columns: List[str]):
        self.columns = columns
    
    def __str__(self) -> str:
        columns_str = ", ".join(self.columns)
        return f"GROUP BY {columns_str}"


class HavingNode(ASTNode):
    """Represents a HAVING clause in SQL."""
    
    def __init__(self, where_clause: WhereClause):
        self.where_clause = where_clause
    
    def __str__(self) -> str:
        return f"HAVING {self.where_clause}"


class AggregateFunctionNode(ASTNode):
    """Represents aggregate functions like COUNT, SUM, AVG, etc."""
    
    def __init__(self, function_name: str, column: str, distinct: bool = False):
        self.function_name = function_name.upper()
        self.column = column
        self.distinct = distinct
    
    def __str__(self) -> str:
        distinct_part = "DISTINCT " if self.distinct else ""
        return f"{self.function_name}({distinct_part}{self.column})"


class SQLQuery(ASTNode):
    """Represents a complete SQL query with all its clauses."""
    
    def __init__(self):
        self.select_node: Optional[SelectNode] = None
        self.from_node: Optional[FromNode] = None
        self.join_nodes: List[JoinNode] = []
        self.where_node: Optional[WhereNode] = None
        self.group_by_node: Optional[GroupByNode] = None
        self.having_node: Optional[HavingNode] = None
        self.order_by_node: Optional[OrderByNode] = None
        self.limit_node: Optional[LimitNode] = None
        self.output_file: Optional[str] = None  # For CSV redirection
    
    def __str__(self) -> str:
        """Reconstruct the SQL query string."""
        parts = []
        
        if self.select_node:
            parts.append(str(self.select_node))
        
        if self.from_node:
            parts.append(str(self.from_node))
        
        for join_node in self.join_nodes:
            parts.append(str(join_node))
        
        if self.where_node:
            parts.append(str(self.where_node))
        
        if self.group_by_node:
            parts.append(str(self.group_by_node))
        
        if self.having_node:
            parts.append(str(self.having_node))
        
        if self.order_by_node:
            parts.append(str(self.order_by_node))
        
        if self.limit_node:
            parts.append(str(self.limit_node))
        
        query = " ".join(parts)
        
        if self.output_file:
            query += f" > {self.output_file}"
        
        return query
    
    def get_referenced_tables(self) -> List[TableReference]:
        """Get all table references in the query."""
        tables = []
        
        if self.from_node:
            tables.extend(self.from_node.tables)
        
        for join_node in self.join_nodes:
            tables.append(join_node.join_clause.right_table)
        
        return tables
    
    def get_selected_columns(self) -> List[Union[str, ColumnReference]]:
        """Get all selected columns."""
        if self.select_node:
            return self.select_node.columns
        return []
    
    def has_aggregates(self) -> bool:
        """Check if query contains aggregate functions."""
        if not self.select_node:
            return False
        
        for column in self.select_node.columns:
            if isinstance(column, AggregateFunctionNode):
                return True
        
        return False
    
    def is_simple_select(self) -> bool:
        """Check if this is a simple SELECT query without joins or complex operations."""
        return (
            self.select_node is not None and
            self.from_node is not None and
            len(self.from_node.tables) == 1 and
            not self.join_nodes and
            not self.group_by_node and
            not self.having_node and
            not self.has_aggregates()
        )