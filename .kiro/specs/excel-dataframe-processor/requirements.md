# Requirements Document

## Introduction

This feature involves creating a Python application with a REPL (Read-Eval-Print Loop) interface that can load Excel files into DataFrames and perform SQL-like operations including SELECT queries and JOIN operations between sheets from the same or different Excel files. The application will use uv for dependency management and provide a simple SQL-based query language for data manipulation. The results can be exported as CSV files.

## Requirements

### Requirement 1

**User Story:** As a data analyst, I want to load Excel files into DataFrames, so that I can work with spreadsheet data programmatically.

#### Acceptance Criteria

1. WHEN a user specifies an Excel file path THEN the system SHALL load the file and make all sheets accessible
2. WHEN a user specifies a sheet number or name THEN the system SHALL load that specific sheet into a DataFrame
3. IF an Excel file does not exist THEN the system SHALL provide a clear error message
4. WHEN loading a sheet THEN the system SHALL preserve data types where possible
5. WHEN an invalid sheet number or name is specified THEN the system SHALL provide a helpful error message

### Requirement 2

**User Story:** As a data analyst, I want to join data from two sheets using SQL JOIN syntax, so that I can combine related data from different sources using familiar database operations.

#### Acceptance Criteria

1. WHEN using implicit joins THEN the system SHALL support "FROM table1, table2 WHERE condition" syntax for inner joins
2. WHEN using explicit joins THEN the system SHALL support "FROM table1 INNER JOIN table2 ON condition" syntax
3. WHEN using left joins THEN the system SHALL support "FROM table1 LEFT JOIN table2 ON condition" syntax
4. WHEN specifying join types THEN the system SHALL support INNER JOIN, LEFT JOIN, RIGHT JOIN, and FULL OUTER JOIN
5. WHEN using JOIN syntax THEN the system SHALL support both "JOIN" (defaulting to INNER) and explicit "INNER JOIN"
4. WHEN sheets are from different Excel files THEN the system SHALL handle cross-file joins seamlessly
5. IF join columns do not exist in the specified sheets THEN the system SHALL provide clear error messages
6. WHEN join columns have different data types THEN the system SHALL attempt type coercion or provide warnings
7. WHEN the join operation completes THEN the system SHALL return results in tabular format

### Requirement 3

**User Story:** As a data analyst, I want a REPL interface with Oracle-like SQL query capabilities and database directory support, so that I can interactively explore and manipulate Excel data using familiar SQL syntax.

#### Acceptance Criteria

1. WHEN starting the application THEN the system SHALL accept --db <foldername> parameter to specify database directory
2. WHEN using SELECT queries THEN the system SHALL support "SELECT column1, column2 FROM excelfile.sheetname" syntax
3. WHEN selecting all columns THEN the system SHALL support "SELECT * FROM excelfile.sheetname" syntax
4. WHEN joining sheets THEN the system SHALL support "SELECT column1, column2 FROM excelfile1.sheet1, excelfile2.sheet2 WHERE condition" syntax
5. WHEN using WHERE clauses THEN the system SHALL support filtering conditions and comparisons
6. WHEN limiting results THEN the system SHALL support "WHERE ROWNUM < 100" syntax for first N rows
7. WHEN ordering results THEN the system SHALL support "ORDER BY column_name ASC/DESC" syntax
8. WHEN referencing sheets THEN the system SHALL treat "excelfile.sheetname" like Oracle's "schema.tablename" notation
9. WHEN query syntax is invalid THEN the system SHALL provide helpful error messages and suggestions
10. WHEN queries execute successfully THEN the system SHALL display results in a readable tabular format
11. WHEN using arrow keys THEN the system SHALL support up arrow for previous commands and down arrow for next commands in history
12. WHEN commands are entered THEN the system SHALL maintain persistent history in .history file within the db directory

### Requirement 4

**User Story:** As a data analyst, I want to export query results as CSV files directly from the REPL, so that I can save results using simple shell-like redirection syntax.

#### Acceptance Criteria

1. WHEN using redirection syntax THEN the system SHALL support "SELECT ... > filename.csv" to export results
2. WHEN exporting to CSV THEN the system SHALL properly escape all CSV special characters including commas, double quotes, single quotes, newlines, and carriage returns
3. WHEN CSV contains commas, quotes, or newlines THEN the system SHALL wrap fields in double quotes
4. WHEN CSV contains double quotes THEN the system SHALL escape them by doubling the quotes (e.g., "He said ""Hello""")
5. WHEN CSV contains newlines or carriage returns THEN the system SHALL preserve them within quoted fields
6. WHEN CSV contains leading or trailing whitespace THEN the system SHALL preserve it by quoting the field
5. WHEN specifying an output path THEN the system SHALL create the file at that location
6. IF the output directory does not exist THEN the system SHALL create it automatically
7. WHEN export is complete THEN the system SHALL confirm successful file creation with row count
8. WHEN the CSV file already exists THEN the system SHALL ask for confirmation before overwriting

### Requirement 5

**User Story:** As a developer, I want the application to use uv for dependency management, so that I can have reproducible and fast dependency resolution.

#### Acceptance Criteria

1. WHEN setting up the project THEN the system SHALL use uv for all dependency management
2. WHEN installing dependencies THEN the system SHALL use pyproject.toml for configuration
3. WHEN running the application THEN the system SHALL work with uv-managed virtual environments
4. WHEN adding new dependencies THEN the system SHALL use uv add command
5. WHEN the project is shared THEN the system SHALL include proper lock files for reproducibility

### Requirement 6

**User Story:** As a user, I want clear error handling and logging, so that I can understand what went wrong and how to fix issues.

#### Acceptance Criteria

1. WHEN an error occurs THEN the system SHALL provide descriptive error messages
2. WHEN file operations fail THEN the system SHALL indicate the specific file and reason
3. WHEN data type issues occur THEN the system SHALL suggest possible solutions
4. WHEN operations are successful THEN the system SHALL provide confirmation messages
5. WHEN debugging is needed THEN the system SHALL support verbose logging modes

### Requirement 7

**User Story:** As a data analyst, I want comprehensive SQL query features, so that I can perform complex data analysis operations similar to Oracle SQL.

#### Acceptance Criteria

1. WHEN using SELECT statements THEN the system SHALL support column aliases with AS keyword
2. WHEN filtering data THEN the system SHALL support comparison operators (=, !=, <, >, <=, >=)
3. WHEN filtering data THEN the system SHALL support logical operators (AND, OR, NOT)
4. WHEN using ROWNUM THEN the system SHALL support "WHERE ROWNUM <= N" for limiting results
5. WHEN ordering results THEN the system SHALL support multiple columns in ORDER BY clause
6. WHEN ordering results THEN the system SHALL support both ASC and DESC keywords
7. WHEN using aggregate functions THEN the system SHALL support COUNT, SUM, AVG, MIN, MAX
8. WHEN grouping data THEN the system SHALL support GROUP BY clause with aggregate functions

### Requirement 8

**User Story:** As a data analyst, I want a colorful and visually appealing REPL interface, so that I can easily read and interpret query results with clear visual formatting.

#### Acceptance Criteria

1. WHEN displaying query results THEN the system SHALL use different colors for different columns
2. WHEN showing tabular data THEN the system SHALL use ASCII art table formatting with proper borders
3. WHEN displaying columns THEN the system SHALL pad columns to ensure proper alignment
4. WHEN showing headers THEN the system SHALL highlight column headers with distinct colors or formatting
5. WHEN displaying data types THEN the system SHALL use color coding to distinguish between text, numbers, and dates
6. WHEN showing large tables THEN the system SHALL maintain consistent column widths and alignment
7. WHEN the terminal supports colors THEN the system SHALL automatically enable colorful output
8. WHEN colors are not supported THEN the system SHALL gracefully fall back to plain ASCII tables

### Requirement 9

**User Story:** As a data analyst, I want database management commands, so that I can easily discover and load Excel files from my database directory.

#### Acceptance Criteria

1. WHEN using "SHOW DB" command THEN the system SHALL display all Excel files and their sheet names in the database directory
2. WHEN using "LOAD DB" command THEN the system SHALL load all Excel files in the database directory into memory as DataFrames
3. WHEN using "HELP" command THEN the system SHALL display helpful examples and detailed information about available commands
4. WHEN files are loaded THEN the system SHALL show progress and confirmation of successful loading
5. WHEN displaying database contents THEN the system SHALL show file names, sheet names, and basic metadata
6. WHEN memory usage is high THEN the system SHALL provide warnings and memory usage information

### Requirement 10

**User Story:** As a data scientist, I want to use the Excel DataFrame Processor directly in Jupyter notebooks and Python scripts, so that I can integrate Excel querying capabilities into my data analysis workflows.

#### Acceptance Criteria

1. WHEN importing the package in Python THEN the system SHALL provide a programmatic interface for Excel querying
2. WHEN using in Jupyter notebooks THEN the system SHALL display results in rich HTML tables with proper formatting
3. WHEN creating an ExcelProcessor instance THEN the system SHALL accept a database directory parameter
4. WHEN executing SQL queries programmatically THEN the system SHALL return pandas DataFrames
5. WHEN using in notebooks THEN the system SHALL support magic commands for convenient SQL execution
6. WHEN displaying results THEN the system SHALL automatically format tables for notebook display
7. WHEN exporting results THEN the system SHALL support direct DataFrame operations and CSV export
8. WHEN working with multiple files THEN the system SHALL maintain the same file.sheet notation as the REPL
9. WHEN errors occur THEN the system SHALL provide clear Python exceptions with helpful messages
10. WHEN using autocompletion THEN the system SHALL provide hints for available files and sheets

### Requirement 11

**User Story:** As a developer, I want sample Excel files, comprehensive tests, and example notebooks, so that I can verify the application works correctly and demonstrate its capabilities.

#### Acceptance Criteria

1. WHEN the project is set up THEN the system SHALL include sample Excel files with realistic data
2. WHEN sample files are provided THEN the system SHALL include files with multiple sheets and different data types
3. WHEN testing the application THEN the system SHALL include test cases for all major functionality
4. WHEN running tests THEN the system SHALL verify SELECT, JOIN, WHERE, ORDER BY, SHOW DB, LOAD DB, and EXPORT operations
5. WHEN demonstrating the application THEN the system SHALL include example queries that work with sample data
6. WHEN tests are executed THEN the system SHALL validate both successful operations and error handling
7. WHEN providing examples THEN the system SHALL include a comprehensive Jupyter notebook with usage examples
8. WHEN using notebooks THEN the system SHALL demonstrate both programmatic API and magic command usage
9. WHEN showing examples THEN the system SHALL include data visualization and analysis workflows
10. WHEN documenting features THEN the system SHALL provide clear examples for both REPL and notebook usage