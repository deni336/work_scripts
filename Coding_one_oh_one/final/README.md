# Main Application Class for ToDo List Application
## Summary
A main application class that provides both CLI and GUI interfaces for a ToDo list application. It initializes core components (config, logger, event handler, database) and offers a command-line interface with task management commands, while also supporting GUI mode switching.

___
## Example Usage
```python
# Initialize and run with default GUI mode
app = MainApp()
gui = AppGUI(config=app.config, logger=app.logger, event_handler=app.event_handler)
gui.run()

# Initialize and run CLI mode
config = ConfigHandler()
config.set('Application', 'mode', 'cli')
app = MainApp(config=config)
app.cli()

# CLI commands available:
# add - Add a new task
# remove - Remove task by ID
# list - Display all tasks
# clear - Clear all tasks
# gui - Switch to GUI mode
# exit - Exit application
```

___
## Code Analysis
### Inputs
- `config`: Optional ConfigHandler instance for application configuration
- `logger`: Optional logger instance from GlobalLogger
- `event_handler`: Optional EventHandler instance for process management
### Flow
1. Initializes core components (config, logger, event_handler, database_handler) with defaults if not provided
2. In CLI mode, enters an interactive loop accepting commands (add, remove, list, clear, gui, exit)
3. Each command performs database operations through the database handler and logs actions
4. GUI command switches from CLI to GUI mode by creating and running an AppGUI instance
5. Main execution block determines startup mode from config and launches appropriate interface
### Outputs
- CLI interface with interactive command prompt
- Task management operations (add, remove, list, clear tasks)
- GUI application launch capability
- Comprehensive logging of all operations and user interactions



# Config Handler Class for ToDo List Application

## Summary
The code defines a `ConfigHandler` class that manages application configuration using a configuration file. It initializes with a default configuration, ensures all default settings are present, and provides methods to read and write configuration options.

___
## Example Usage
```python
config_handler = ConfigHandler()
config_handler.set('Logging', 'loglevel', 'DEBUG')
loglevel = config_handler.get('Logging', 'loglevel')
print(loglevel)  # Output: DEBUG
```

___
## Code Analysis
### Inputs
- `config_file`: Optional path to a configuration file.
- `section`: The section in the configuration file.
- `option`: The option within the section.
- `value`: The value to set for a given option.
- `fallback`: A fallback value if the option is not found.
### Flow
1. The `ConfigHandler` class is initialized with an optional configuration file path.
2. If the configuration file does not exist, a default configuration is written.
3. The class ensures all default configuration options are present.
4. Methods are provided to get and set configuration options, including type-specific getters for integers and floats.
### Outputs
- Returns configuration values as strings, integers, or floats.
- Writes updated configuration to the file.
- Returns the entire configuration as a nested dictionary.


# Database Handler Class for ToDo List Application

## Summary
The code snippet defines a `DatabaseHandler` class that manages SQLite database connections and operations. It includes methods for connecting to and closing the database, executing queries, and fetching results. The class uses a logger to record actions and an event handler for additional processing.

___
## Example Usage
```python
config = {'Database': {'dbpath': 'example.db'}}
logger = Logger()  # Assume Logger is a predefined class
event_handler = EventHandler()  # Assume EventHandler is a predefined class

db_handler = DatabaseHandler(config, logger, event_handler)
db_handler.connect()
db_handler.execute_query("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
db_handler.execute_query("INSERT INTO users (name) VALUES (?)", ("Alice",))
results = db_handler.fetch_all("SELECT * FROM users")
print(results)  # Expected output: [(1, 'Alice')]
db_handler.close()
```

___
## Code Analysis
### Inputs
- `config`: A configuration object containing database settings, specifically the database path.
- `logger`: An object for logging information, warnings, and errors.
- `event_handler`: An object for handling events, though not used in the snippet.
### Flow
1. The `DatabaseHandler` class is initialized with configuration, logger, and event handler.
2. The `connect` method establishes a connection to the SQLite database using the path from the configuration.
3. The `close` method closes the database connection if it exists.
4. The `execute_query` method runs a SQL query with optional parameters and commits changes.
5. The `fetch_all` method executes a query and returns all results.
### Outputs
- Logs information about database connections and operations.
- Executes SQL queries and returns results from `fetch_all`.

# Event Handler Class for ToDo List Application

## Summary
The `EventHandler` class is responsible for managing process events by registering, removing, and querying events based on their names and process IDs (PIDs). It utilizes a logger to record actions and warnings related to event management.

___
## Example Usage
```python
event_handler = EventHandler()

# Register events
event_handler.register_event("ProcessA", 1234)
event_handler.register_event("ProcessB", 5678)

# Check if an event exists
print(event_handler.has_event("ProcessA"))  # Output: True

# Get PID of an event
print(event_handler.get_pid("ProcessA"))  # Output: 1234

# List all events
print(event_handler.list_events())  # Output: {'ProcessA': 1234, 'ProcessB': 5678}

# Remove an event
event_handler.remove_event("ProcessA")

# Clear all events
event_handler.clear_events()
```

___
## Code Analysis
### Inputs
- `name`: The name of the event to register, remove, or query.
- `pid`: The process ID associated with the event.
### Flow
1. **Initialization**: The `EventHandler` is initialized with an optional logger. If no logger is provided, it defaults to using the `GlobalLogger`.
2. **Register Event**: The `register_event` method adds an event with a given name and PID to the internal dictionary `_events` and logs the action.
3. **Remove Event**: The `remove_event` method deletes an event by name from `_events` and logs the action. If the event does not exist, it logs a warning.
4. **Get PID**: The `get_pid` method retrieves the PID for a given event name.
5. **List Events**: The `list_events` method returns a copy of the `_events` dictionary.
6. **Clear Events**: The `clear_events` method removes all events from `_events` and logs the action.
7. **Check Event Existence**: The `has_event` method checks if an event with a given name exists in `_events`.
### Outputs
- Logs actions and warnings related to event registration and removal.
- Provides access to event PIDs and the list of registered events.

# Global Logger Class for ToDo List Application

## Summary
This code defines a `GlobalLogger` class that provides a method to create and configure a logger with both file and console handlers. The logger's configuration is based on settings from a configuration file.

___
## Example Usage
```python
from global_logger import GlobalLogger

logger = GlobalLogger.get_logger("my_logger")
logger.info("This is an info message.")
```

___
## Code Analysis
### Inputs
- `name`: The name of the logger to be created.
### Flow
1. Retrieve the base path for logging from the default configuration path.
2. Get the logging path and log level from the configuration.
3. Create the log directory if it doesn't exist.
4. Create a log file named with the current date.
5. Set up a file handler and a console handler with specific formatting.
6. Clear any existing handlers from the logger to prevent duplicate logs.
7. Add the new file and console handlers to the logger.
8. Return the configured logger.
### Outputs
- A configured logger instance with file and console handlers.

# GUI Application Class for ToDo List Application

## Summary
The code defines a class `AppGUI` that creates a graphical user interface (GUI) for a ToDo List application using Tkinter. It manages tasks by adding, removing, and clearing them, and interacts with a database to persist task data.

___
## Example Usage
```python
import logging
from src.config_handler import ConfigHandler
from src.db import DatabaseHandler

logger = logging.getLogger(__name__)
config = ConfigHandler()
event_handler = None  # Replace with actual event handler if needed

app = AppGUI(logger, config, event_handler)
app.run()
```

___
## Code Analysis
### Inputs
- `logger`: A logging object for logging messages.
- `config`: A configuration handler object for managing configurations.
- `event_handler`: An event handler object for handling events.
### Flow
1. Initializes the `AppGUI` class with logger, config, and event handler.
2. Sets up the main Tkinter window and widgets for task management.
3. Binds buttons and key events to functions for adding, removing, and clearing tasks.
4. Interacts with a database to store and retrieve tasks.
5. Provides a button to open the configuration file.
### Outputs
- A GUI window for managing a ToDo list.
- Logs messages for actions performed.
- Database entries for tasks.
