import os, sys
from tkinter import Tk, Label, Button, Entry, Listbox, Scrollbar, messagebox
from src.config_handler import ConfigHandler, get_default_config_path
from src.db import DatabaseHandler

class AppGUI:
   def __init__(self, logger, config, event_handler):
      self.logger = logger
      self.config = config
      self.event_handler = event_handler
      self.db_handler = DatabaseHandler(self.config, self.logger, self.event_handler)
      self.default_config_path = get_default_config_path()
   
   def run(self):
      self.logger.info("Starting GUI application...")

      self.root = Tk()
      self.root.title("ToDo List Application")
      self.setup_widgets()
      self.root.mainloop()
      self.logger.info("GUI application started successfully.")

   def setup_widgets(self):
      Label(self.root, text="ToDo List Application").pack(pady=10)

      self.task_entry = Entry(self.root, width=50)
      self.task_entry.pack(pady=5)

      self.add_button = Button(self.root, text="Add Task", command=self.add_task)
      self.add_button.pack(pady=5)
      self.root.bind('<Return>', lambda event: self.add_task())

      self.remove_button = Button(self.root, text="Remove Task", command=self.remove_task)
      self.remove_button.pack(pady=5)

      self.clear_button = Button(self.root, text="Clear Tasks", command=self.clear_tasks)
      self.clear_button.pack(pady=5)

      def open_config():
         if sys.platform == "win32":
            os.startfile(self.default_config_path)
         elif sys.platform == "darwin":  # macOS
            subprocess.Popen(["open", self.default_config_path])
         else:  # Linux and others
            subprocess.Popen(["xdg-open", self.default_config_path])

      self.config_button = Button(self.root, text="Configuration", command=open_config)
      self.config_button.pack(pady=5)

      self.task_listbox = Listbox(self.root, width=50, height=10)
      self.task_listbox.pack(pady=5)

      self.scrollbar = Scrollbar(self.root)
      self.scrollbar.pack(side='right', fill='y')
      self.task_listbox.config(yscrollcommand=self.scrollbar.set)
      self.scrollbar.config(command=self.task_listbox.yview)
      self.db_handler.execute_query("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, task TEXT)")
      task_list = self.db_handler.fetch_all("SELECT * FROM tasks")
      for task in task_list:
         self.task_listbox.insert('end', task[1])

   def add_task(self):
      task = self.task_entry.get()
      if task:
         self.task_listbox.insert('end', task)
         self.task_entry.delete(0, 'end')
         self.db_handler.execute_query("INSERT INTO tasks (task) VALUES (?)", (task,))
         self.logger.info(f"Task added: {task}")
      else:
         messagebox.showwarning("Input Error", "Please enter a task.")
         self.logger.warning("Attempted to add an empty task.")
   
   def remove_task(self):
      selected_task_index = self.task_listbox.curselection()
      if selected_task_index:
         task = self.task_listbox.get(selected_task_index)
         self.task_listbox.delete(selected_task_index)
         self.db_handler.execute_query("DELETE FROM tasks WHERE task = ?", (task,))
         self.logger.info(f"Task removed: {task}")
      else:
         messagebox.showwarning("Selection Error", "Please select a task to remove.")
         self.logger.warning("Attempted to remove a task without selection.")
   
   def clear_tasks(self):
      self.task_listbox.delete(0, 'end')
      self.db_handler.execute_query("DELETE FROM tasks")
      self.logger.info("All tasks cleared.")
      messagebox.showinfo("Clear Tasks", "All tasks have been cleared.")
   

      