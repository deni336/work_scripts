from src.global_logger import GlobalLogger
from src.config_handler import ConfigHandler, get_default_base_path
from src.event_handler import EventHandler
from src.gui import AppGUI
from src.db import DatabaseHandler

class MainApp:
   def __init__(self, config=None, logger=None, event_handler=None):
      self.config = config or ConfigHandler()
      self.logger = logger or GlobalLogger.get_logger(__name__)
      self.event_handler = event_handler or EventHandler(self.logger)
      self.database_handler = DatabaseHandler(self.config, self.logger, self.event_handler)

   def cli(self):
      """Command Line Interface for the application."""
      self.logger.info("Starting CLI application...")
      print("Welcome to the ToDo List Application!")
      print("Use the GUI for a better experience.")
      self.logger.info("CLI application started successfully.")
      self.cli_loop()
   
   def cli_loop(self):
      """Main loop for the CLI application."""
      while True:
         command = input("Enter a command (add, remove, list, clear, gui, exit): ").strip().lower()
         if command == "add":
            task = input("Enter the task to add: ").strip()
            if task:
               self.database_handler.execute_query("INSERT INTO tasks (task) VALUES (?)", (task,))
               self.logger.info(f"Task added: {task}")
               print(f"Task '{task}' added successfully.")
            else:
               self.logger.warning("No task entered for addition.")
               print("No task entered. Please try again.")
         elif command == "remove":
            task_id = input("Enter the task ID to remove: ").strip()
            if task_id.isdigit():
               self.database_handler.execute_query("DELETE FROM tasks WHERE id = ?", (task_id,))
               self.logger.info(f"Task with ID {task_id} removed.")
               print(f"Task with ID {task_id} removed successfully.")
            else:
               self.logger.warning(f"Invalid task ID entered: {task_id}")
               print("Invalid task ID. Please try again.")
         elif command == "list":
            tasks = self.database_handler.fetch_all("SELECT * FROM tasks")
            if tasks:
               print("Current tasks:")
               for task in tasks:
                  print(f"ID: {task[0]}, Task: {task[1]}")
            else:
               self.logger.info("No tasks found.")
               print("No tasks found.")
         elif command == "clear":
            confirm = input("Are you sure you want to clear all tasks? (yes/no): ").strip().lower()
            if confirm == "yes":
               self.database_handler.execute_query("DELETE FROM tasks")
               self.logger.info("All tasks cleared.")
               print("All tasks cleared successfully.")
            else:
               self.logger.info("Task clearing operation cancelled by user.")
               print("Task clearing operation cancelled.")
         elif command == "gui":
            self.logger.info("Switching to GUI mode.")
            print("Switching to GUI mode. Please wait...")
            gui = AppGUI(config=self.config, logger=self.logger, event_handler=self.event_handler)
            gui.run()
            break
         elif command == "exit":
            self.logger.info("Exiting CLI application.")
            print("Exiting the application. Goodbye!")
            break
         else:
            self.logger.warning(f"Invalid command entered: {command}")
            print("Invalid command. Please try again.")

if __name__ == "__main__":
   config = ConfigHandler()
   logger = GlobalLogger.get_logger(__name__)
   event_handler = EventHandler(logger)

   app = MainApp(config=config, logger=logger, event_handler=event_handler)
   if config.get('Application', 'mode', fallback='gui') == 'cli':
      app.cli()
   else:
      logger.info("Starting GUI application...")
   gui = AppGUI(config=config, logger=logger, event_handler=event_handler)
   gui.run()

   app.logger.info("Application started successfully.")
