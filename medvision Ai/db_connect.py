import mysql.connector
from mysql.connector import Error
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """MySQL Database Connection Handler"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Establish connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                port=Config.MYSQL_PORT
            )
            self.cursor = self.connection.cursor(dictionary=True)
            logger.info("✓ Database connection established successfully")
            return True
        except Error as e:
            logger.error(f"✗ Error connecting to database: {e}")
            return False
    
    def execute_query(self, query, params=None):
        """Execute a single query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            logger.info("✓ Query executed successfully")
            return True
        except Error as e:
            logger.error(f"✗ Error executing query: {e}")
            self.connection.rollback()
            return False
    
    def fetch_all(self, query, params=None):
        """Fetch all records from query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"✗ Error fetching records: {e}")
            return None
    
    def fetch_one(self, query, params=None):
        """Fetch single record from query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except Error as e:
            logger.error(f"✗ Error fetching record: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            logger.info("✓ Database connection closed")

# Create global database instance
db = DatabaseConnection()
