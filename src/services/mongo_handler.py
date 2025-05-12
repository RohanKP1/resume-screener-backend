from pymongo import MongoClient, errors
from src.core.custom_logger import CustomLogger
from src.core.config import Config

class MongoHandler:
    """
    Enterprise-level MongoDB handler with robust logging and configuration.
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        db_name: str = None,
        logger: CustomLogger = None
    ):
        self.logger = logger or CustomLogger("MongoHandler")
        self.host = host or getattr(Config, "MONGO_HOST", "localhost")
        self.port = port or int(getattr(Config, "MONGO_PORT", 27017))
        self.username = username or getattr(Config, "MONGO_INITDB_ROOT_USERNAME", "root")
        self.password = password or getattr(Config, "MONGO_INITDB_ROOT_PASSWORD", "password")
        self.db_name = db_name or getattr(Config, "MONGO_DB", "admin")

        try:
            self.client = MongoClient(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                serverSelectionTimeoutMS=5000
            )
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.logger.info("MongoDB connection established successfully.")
        except errors.PyMongoError as e:
            self.logger.error(f"Error connecting to MongoDB: {e}")
            raise

    def insert_one(self, collection: str, document: dict):
        try:
            result = self.db[collection].insert_one(document)
            self.logger.info(f"Inserted document with id: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            self.logger.error(f"Insert failed: {e}")
            raise

    def find_one(self, collection: str, query: dict):
        try:
            result = self.db[collection].find_one(query)
            self.logger.debug(f"Find one result: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Find one failed: {e}")
            raise

    def find_many(self, collection: str, query: dict):
        try:
            results = list(self.db[collection].find(query))
            self.logger.debug(f"Find many results: {results}")
            return results
        except Exception as e:
            self.logger.error(f"Find many failed: {e}")
            raise

    def update_one(self, collection: str, query: dict, update: dict):
        try:
            result = self.db[collection].update_one(query, {'$set': update})
            self.logger.info(f"Updated {result.modified_count} document(s)")
            return result.modified_count
        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            raise

    def delete_one(self, collection: str, query: dict):
        try:
            result = self.db[collection].delete_one(query)
            self.logger.info(f"Deleted {result.deleted_count} document(s)")
            return result.deleted_count
        except Exception as e:
            self.logger.error(f"Delete failed: {e}")
            raise

    def close(self):
        try:
            self.client.close()
            self.logger.info("MongoDB connection closed.")
        except Exception as e:
            self.logger.error(f"Error closing MongoDB connection: {e}")

# Example usage:
def test_mongo_handler():
    """
    Test the MongoHandler class with a custom logger.
    """
    logger = CustomLogger("MongoHandlerTest")
    mongo_handler = MongoHandler(logger=logger)
    try:
        # Insert a document
        doc_id = mongo_handler.insert_one("test_collection", {"name": "example", "value": 123})
        # Find the document
        doc = mongo_handler.find_one("test_collection", {"_id": doc_id})
        logger.info(f"Fetched document: {doc}")
        # Update the document
        mongo_handler.update_one("test_collection", {"_id": doc_id}, {"value": 456})
        # Delete the document
        mongo_handler.delete_one("test_collection", {"_id": doc_id})
    finally:
        mongo_handler.close()