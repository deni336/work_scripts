import sqlite3

class DatabaseHandler:
   def __init__(self, config, logger, event_handler):
      self.config = config
      self.logger = logger
      self.event_handler = event_handler
      self.db_path = config.get('Database', 'dbpath')

   def connect(self):
      """Connect to the database."""
      self.logger.info(f"Connecting to database at {self.db_path}")
  
      self.connection = sqlite3.connect(self.db_path)
      self.logger.info("Database connection established.")

   def close(self):
      """Close the database connection."""
      if hasattr(self, 'connection'):
         self.connection.close()
         self.logger.info("Database connection closed.")
      else:
         self.logger.warning("No database connection to close.")
      
   def execute_query(self, query, params=None):
      """Execute a query against the database."""
      if not hasattr(self, 'connection'):
         self.connect()
      
      cursor = self.connection.cursor()
      try:
         self.logger.info(f"Executing query: {query} with params: {params}")
         cursor.execute(query, params or ())
         self.connection.commit()
         self.logger.info("Query executed successfully.")
      except sqlite3.Error as e:
         self.logger.error(f"Database error: {e}")
         raise
      finally:
         cursor.close()
      
   def fetch_all(self, query, params=None):
      """Fetch all results from a query."""
      if not hasattr(self, 'connection'):
         self.connect()
      
      cursor = self.connection.cursor()
      try:
         self.logger.info(f"Fetching all results for query: {query} with params: {params}")
         cursor.execute(query, params or ())
         results = cursor.fetchall()
         self.logger.info(f"Fetched {len(results)} results.")
         return results
      except sqlite3.Error as e:
         self.logger.error(f"Database error: {e}")
         raise
      finally:
         cursor.close()