import os
import sys
import time
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import threading

# Try to import colorama for cross-platform colored output
try:
    from colorama import init, Fore, Back, Style
    init()  # Initialize colorama
    HAS_COLOR = True
except ImportError:
    # Create dummy color constants if colorama is not available
    class DummyColor:
        def __getattr__(self, name):
            return ""
    
    Fore = DummyColor()
    Back = DummyColor()
    Style = DummyColor()
    HAS_COLOR = False

# Try to import rich for progress bars and tables
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.table import Table
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False

# Configure logging
logger = logging.getLogger("cli")

# Default verbosity level
DEFAULT_VERBOSITY = 1  # 0=quiet, 1=normal, 2=verbose, 3=debug

class CLI:
    """CLI interface handler for the reconnaissance framework."""
    
    def __init__(self, verbosity: int = DEFAULT_VERBOSITY):
        """
        Initialize the CLI handler.
        
        Args:
            verbosity: The verbosity level
                0 = quiet (errors only)
                1 = normal (errors + warnings + basic info)
                2 = verbose (all info messages)
                3 = debug (all messages including debug)
        """
        self.verbosity = verbosity
        self.start_time = time.time()
        self._setup_logging()
        
        # Store active progress bars
        self.active_progress = {}
        self.progress_lock = threading.Lock()
        
    def _setup_logging(self):
        """Configure logging based on verbosity level."""
        root_logger = logging.getLogger()
        
        # Set logging level based on verbosity
        if self.verbosity == 0:
            level = logging.ERROR
        elif self.verbosity == 1:
            level = logging.WARNING
        elif self.verbosity == 2:
            level = logging.INFO
        else:  # 3 or higher
            level = logging.DEBUG
            
        # Configure root logger to use our formatter
        root_logger.setLevel(level)
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Create formatter and add it to handler
        formatter = CLIFormatter()
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        root_logger.addHandler(console_handler)
        
        # Set specific levels for noisy modules
        if self.verbosity < 3:
            # Reduce verbosity of common libraries
            logging.getLogger("httpx").setLevel(logging.WARNING)
            logging.getLogger("urllib3").setLevel(logging.WARNING)
            logging.getLogger("requests").setLevel(logging.WARNING)
            logging.getLogger("websockets").setLevel(logging.WARNING)
        
    def header(self, text: str):
        """Display a header with a title."""
        if self.verbosity == 0:
            return
            
        title = f" {text} "
        if HAS_RICH:
            console.print(Panel(title, style="bold blue"))
        else:
            width = min(os.get_terminal_size().columns, 80)
            padding = max(width - len(title), 0)
            left_padding = padding // 2
            right_padding = padding - left_padding
            
            print()
            print(f"{Fore.BLUE}{Style.BRIGHT}{'-' * left_padding}{title}{'-' * right_padding}{Style.RESET_ALL}")
            print()
    
    def subheader(self, text: str):
        """Display a subheader."""
        if self.verbosity == 0:
            return
            
        if HAS_RICH:
            console.print(f"[bold cyan]{text}[/bold cyan]")
        else:
            print(f"{Fore.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}")
    
    def info(self, text: str):
        """Display an information message."""
        if self.verbosity < 1:
            return
            
        if HAS_RICH:
            console.print(f"[green]•[/green] {text}")
        else:
            print(f"{Fore.GREEN}•{Style.RESET_ALL} {text}")
    
    def warning(self, text: str):
        """Display a warning message."""
        if self.verbosity < 1:
            return
            
        if HAS_RICH:
            console.print(f"[yellow]⚠[/yellow] {text}")
        else:
            print(f"{Fore.YELLOW}⚠{Style.RESET_ALL} {text}")
    
    def error(self, text: str):
        """Display an error message."""
        if HAS_RICH:
            console.print(f"[bold red]✘[/bold red] {text}")
        else:
            print(f"{Fore.RED}{Style.BRIGHT}✘{Style.RESET_ALL} {text}")
    
    def success(self, text: str):
        """Display a success message."""
        if self.verbosity < 1:
            return
            
        if HAS_RICH:
            console.print(f"[bold green]✓[/bold green] {text}")
        else:
            print(f"{Fore.GREEN}{Style.BRIGHT}✓{Style.RESET_ALL} {text}")
    
    def verbose(self, text: str):
        """Display a verbose message (only shown in verbose mode)."""
        if self.verbosity < 2:
            return
            
        if HAS_RICH:
            console.print(f"[dim]{text}[/dim]")
        else:
            print(f"{Style.DIM}{text}{Style.RESET_ALL}")
    
    def debug(self, text: str):
        """Display a debug message (only shown in debug mode)."""
        if self.verbosity < 3:
            return
            
        if HAS_RICH:
            console.print(f"[dim blue][DEBUG][/dim blue] {text}")
        else:
            print(f"{Style.DIM}{Fore.BLUE}[DEBUG]{Style.RESET_ALL} {text}")
    
    def divider(self):
        """Display a divider line."""
        if self.verbosity == 0:
            return
            
        width = min(os.get_terminal_size().columns, 80)
        if HAS_RICH:
            console.print(f"[dim]{'-' * width}[/dim]")
        else:
            print(f"{Style.DIM}{'-' * width}{Style.RESET_ALL}")
    
    def start_progress(self, task_id: str, description: str, total: Optional[int] = None):
        """
        Start a progress indicator for a task.
        
        Args:
            task_id: Unique identifier for the task
            description: Description of the task
            total: Total steps (if known)
        """
        if self.verbosity == 0:
            return
            
        with self.progress_lock:
            if HAS_RICH:
                # Create columns list based on what's available
                columns = [
                    SpinnerColumn(),
                    TextColumn("[bold blue]{task.description}")
                ]
                
                # Only add bar column if we have a total
                if total is not None:
                    columns.append(BarColumn(complete_style="green"))
                    columns.append(TextColumn("[cyan]{task.completed}/{task.total}"))
                
                # Always add elapsed time
                columns.append(TimeElapsedColumn())
                
                # Create progress with appropriate columns
                progress = Progress(*columns)
                
                task = progress.add_task(description, total=total)
                self.active_progress[task_id] = {
                    "progress": progress,
                    "task": task
                }
                progress.start()
            else:
                # Basic progress indicator for non-rich environments
                print(f"{Fore.BLUE}→ {description}...{Style.RESET_ALL}")
    
    def update_progress(self, task_id: str, advance: int = 1, message: Optional[str] = None):
        """
        Update a progress indicator.
        
        Args:
            task_id: The task identifier
            advance: How much to advance the progress
            message: Optional message to display
        """
        if self.verbosity == 0 or task_id not in self.active_progress:
            return
            
        with self.progress_lock:
            if HAS_RICH:
                task_data = self.active_progress[task_id]
                if message:
                    task_data["progress"].console.print(f"  {message}")
                task_data["progress"].update(task_data["task"], advance=advance)
            elif message and self.verbosity >= 2:
                print(f"  {Fore.CYAN}→{Style.RESET_ALL} {message}")
    
    def stop_progress(self, task_id: str, success: bool = True, message: Optional[str] = None):
        """
        Stop a progress indicator.
        
        Args:
            task_id: The task identifier
            success: Whether the task was successful
            message: Optional completion message
        """
        if self.verbosity == 0 or task_id not in self.active_progress:
            return
            
        with self.progress_lock:
            if HAS_RICH:
                task_data = self.active_progress[task_id]
                task_data["progress"].stop()
                
                if message:
                    if success:
                        console.print(f"[bold green]✓[/bold green] {message}")
                    else:
                        console.print(f"[bold red]✘[/bold red] {message}")
            elif message:
                if success:
                    print(f"{Fore.GREEN}{Style.BRIGHT}✓{Style.RESET_ALL} {message}")
                else:
                    print(f"{Fore.RED}{Style.BRIGHT}✘{Style.RESET_ALL} {message}")
            
            # Remove from active progress
            del self.active_progress[task_id]
    
    def display_results_table(self, headers: List[str], rows: List[List[Any]], title: Optional[str] = None):
        """
        Display results in a table format.
        
        Args:
            headers: List of column headers
            rows: List of rows (each row is a list of values)
            title: Optional table title
        """
        if self.verbosity == 0:
            return
            
        if HAS_RICH:
            table = Table(title=title)
            for header in headers:
                table.add_column(header)
            
            for row in rows:
                table.add_row(*[str(cell) for cell in row])
            
            console.print(table)
        else:
            # Simple ASCII table for non-rich environments
            if title:
                print(f"\n{Style.BRIGHT}{title}{Style.RESET_ALL}")
            
            # Calculate column widths
            col_widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
            
            # Print header
            header_row = " | ".join(f"{h:{w}s}" for h, w in zip(headers, col_widths))
            print(f"\n{Style.BRIGHT}{header_row}{Style.RESET_ALL}")
            print("-" * len(header_row))
            
            # Print rows
            for row in rows:
                print(" | ".join(f"{str(cell):{w}s}" for cell, w in zip(row, col_widths)))
            print()
    
    def display_summary(self, target: str, duration: Optional[float] = None, tasks_completed: int = 0, 
                       findings: Optional[Dict[str, Any]] = None):
        """
        Display a summary of the reconnaissance results.
        
        Args:
            target: The target domain
            duration: How long the scan took (in seconds)
            tasks_completed: Number of completed tasks
            findings: Dictionary of findings by category
        """
        if self.verbosity == 0:
            return
            
        if duration is None:
            duration = time.time() - self.start_time
            
        # Format duration
        if duration < 60:
            duration_str = f"{duration:.1f} seconds"
        elif duration < 3600:
            minutes = int(duration / 60)
            seconds = int(duration % 60)
            duration_str = f"{minutes} min {seconds} sec"
        else:
            hours = int(duration / 3600)
            minutes = int((duration % 3600) / 60)
            duration_str = f"{hours} hr {minutes} min"
            
        # Create summary message
        summary_lines = [
            f"Target: {target}",
            f"Duration: {duration_str}",
            f"Tasks Completed: {tasks_completed}"
        ]
        
        if findings:
            summary_lines.append("\nFindings Summary:")
            for category, items in findings.items():
                if isinstance(items, list):
                    summary_lines.append(f"• {category}: {len(items)} found")
                elif isinstance(items, dict):
                    summary_lines.append(f"• {category}: {len(items)} items")
                else:
                    summary_lines.append(f"• {category}: Completed")
        
        summary_text = "\n".join(summary_lines)
        
        if HAS_RICH:
            console.print(Panel(summary_text, title="[bold green]Reconnaissance Complete[/bold green]", 
                               border_style="green"))
        else:
            self.divider()
            print(f"{Fore.GREEN}{Style.BRIGHT}Reconnaissance Complete{Style.RESET_ALL}")
            print(f"\n{summary_text}\n")
            self.divider()


class CLIFormatter(logging.Formatter):
    """Custom formatter for log messages in the CLI."""
    
    def __init__(self):
        super().__init__("%(message)s")
        
        # Color mapping for log levels
        self.level_colors = {
            logging.DEBUG: Fore.BLUE + Style.DIM,
            logging.INFO: Fore.GREEN,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.RED + Style.BRIGHT
        }
        
        # Emoji mapping for log levels
        self.level_emoji = {
            logging.DEBUG: "🔍",
            logging.INFO: "ℹ️",
            logging.WARNING: "⚠️",
            logging.ERROR: "❌",
            logging.CRITICAL: "🔥"
        }
    
    def format(self, record):
        """Format a log record for display."""
        # Get the original message
        message = super().format(record)
        
        # Don't do any special formatting if we don't have colorama
        if not HAS_COLOR:
            # Just add a timestamp prefix
            timestamp = datetime.now().strftime("%H:%M:%S")
            return f"{timestamp} - {record.levelname.lower()}: {message}"
        
        # Add level color
        level_color = self.level_colors.get(record.levelno, "")
        reset = Style.RESET_ALL
        
        # Format timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Build log message
        if record.levelno == logging.DEBUG:
            # Minimized format for debug messages
            return f"{Style.DIM}{timestamp} - DEBUG:{reset} {message}"
            
        elif record.levelno == logging.INFO:
            # Clean format for info messages
            module = record.name.split('.')[-1]  # Get last part of logger name
            return f"{timestamp} - {Fore.CYAN}{module}{reset}: {message}"
            
        else:
            # Emphasized format for warnings and errors
            return f"{level_color}{timestamp} - {record.levelname}{reset}: {message}"


# Global CLI instance with default verbosity
cli = CLI(DEFAULT_VERBOSITY)

def set_verbosity(level: int):
    """Set the global CLI verbosity level."""
    global cli
    cli = CLI(level)
    return cli 