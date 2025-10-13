"""Main CLI interface for Excel DataFrame Processor."""

import click
import sys
from pathlib import Path
from .repl import ExcelREPL
from .exceptions import DatabaseDirectoryError


@click.command()
@click.option(
    '--db', 
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help='Database directory containing Excel files'
)
@click.option(
    '--memory-limit',
    default=1024.0,
    type=float,
    help='Memory limit in MB for loaded DataFrames (default: 1024)'
)
@click.version_option(version='0.1.0', prog_name='Excel DataFrame Processor')
def main(db: Path, memory_limit: float):
    """
    Excel DataFrame Processor - Query Excel files with SQL syntax.
    
    A REPL interface for executing Oracle-like SQL queries on Excel files.
    Load Excel spreadsheets and query them using familiar SQL commands.
    
    Examples:
    
        excel-processor --db /path/to/excel/files
        
        excel-processor --db sample_data --memory-limit 512
    """
    try:
        # Initialize and start the REPL
        repl = ExcelREPL(db_directory=db, memory_limit_mb=memory_limit)
        repl.start()
        
    except DatabaseDirectoryError as e:
        click.echo(f"❌ Database Directory Error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()