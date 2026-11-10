
import os
import psycopg

def initialize_database():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing")

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            with open("schema.sql", "r", encoding="utf-8") as file:
                schema = file.read()

            cursor.execute(schema)

            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)

            tables = cursor.fetchall()

    print("Database initialization successful!")
    print("\nCreated database tables:")

    for table in tables:
        print("-", table[0])

if __name__ == "__main__":
    initialize_database()
