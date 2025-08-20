import mariadb
from mariadb import Error
from config import get_config

def get_db_connection():
    config = get_config()
    try:
        connection = mariadb.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        return connection
    except Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return None
