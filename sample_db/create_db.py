"""
Script to create sample PostgreSQL database for Text-to-SQL Chatbot.
Creates tables and inserts sample data for testing.
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def create_database():
    """Create the company_db database and tables with sample data."""
    # Connect to PostgreSQL (default database)
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="deepagent"  # Change this to your PostgreSQL password
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Create database
    try:
        cursor.execute("CREATE DATABASE company_db;")
        print("Database 'company_db' created successfully!")
    except psycopg2.errors.DuplicateDatabase:
        print("Database 'company_db' already exists.")
    
    cursor.close()
    conn.close()

    # Connect to the new database
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="deepagent",  # Change this to your PostgreSQL password
        database="company_db"
    )
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        category VARCHAR(100),
        price DECIMAL(10, 2),
        stock INTEGER
    );

    CREATE TABLE IF NOT EXISTS customers (
        customer_id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        email VARCHAR(255),
        city VARCHAR(100)
    );

    CREATE TABLE IF NOT EXISTS orders (
        order_id SERIAL PRIMARY KEY,
        product_id INTEGER REFERENCES products(product_id),
        customer_id INTEGER REFERENCES customers(customer_id),
        quantity INTEGER,
        order_date DATE
    );
    """)
    print("Tables created successfully!")

    # Insert sample data
    cursor.execute("""
    INSERT INTO products (name, category, price, stock) VALUES
    ('Laptop Pro', 'Electronics', 85000.00, 50),
    ('Office Chair', 'Furniture', 12000.00, 30),
    ('Notebook Pack', 'Stationery', 500.00, 200),
    ('Wireless Mouse', 'Electronics', 1500.00, 100),
    ('Standing Desk', 'Furniture', 25000.00, 15),
    ('Mechanical Keyboard', 'Electronics', 5000.00, 75),
    ('Monitor 27"', 'Electronics', 35000.00, 25),
    ('Desk Lamp', 'Furniture', 2000.00, 60),
    ('USB Hub', 'Electronics', 800.00, 150),
    ('Ergonomic Chair', 'Furniture', 18000.00, 20);

    INSERT INTO customers (name, email, city) VALUES
    ('Priya Sharma', 'priya@example.com', 'Delhi'),
    ('Rahul Mehta', 'rahul@example.com', 'Mumbai'),
    ('Anjali Patel', 'anjali@example.com', 'Bangalore'),
    ('Vikram Singh', 'vikram@example.com', 'Chennai'),
    ('Neha Gupta', 'neha@example.com', 'Hyderabad'),
    ('Amit Kumar', 'amit@example.com', 'Pune'),
    ('Sneha Reddy', 'sneha@example.com', 'Kolkata'),
    ('Rajesh Verma', 'rajesh@example.com', 'Ahmedabad');

    INSERT INTO orders (product_id, customer_id, quantity, order_date) VALUES
    (1, 1, 2, '2024-01-15'),
    (3, 2, 5, '2024-01-16'),
    (2, 3, 1, '2024-01-17'),
    (4, 4, 3, '2024-01-18'),
    (5, 5, 1, '2024-01-19'),
    (6, 6, 2, '2024-01-20'),
    (7, 7, 1, '2024-01-21'),
    (8, 8, 4, '2024-01-22'),
    (9, 1, 2, '2024-01-23'),
    (10, 2, 1, '2024-01-24'),
    (1, 3, 1, '2024-01-25'),
    (2, 4, 2, '2024-01-26'),
    (3, 5, 3, '2024-01-27'),
    (4, 6, 1, '2024-01-28'),
    (5, 7, 2, '2024-01-29');
    """)
    print("Sample data inserted successfully!")

    conn.commit()
    cursor.close()
    conn.close()
    print("Database setup completed!")


def create_read_only_user():
    """Create a read-only user for the application."""
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="deepagent",  # Change this to your PostgreSQL password
        database="company_db"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Create read-only user
    try:
        cursor.execute("""
        CREATE USER read_only_user WITH PASSWORD 'deepagent';
        
        -- Grant only SELECT permissions on the database
        GRANT CONNECT ON DATABASE company_db TO read_only_user;
        GRANT USAGE ON SCHEMA public TO read_only_user;
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO read_only_user;
        GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO read_only_user;
        
        -- Ensure future tables also have SELECT permission
        ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT SELECT ON TABLES TO read_only_user;
        """)
        print("Read-only user 'read_only_user' created successfully!")
    except psycopg2.errors.DuplicateObject:
        print("User 'read_only_user' already exists.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    print("Setting up sample database...")
    create_database()
    print("\nCreating read-only user...")
    create_read_only_user()
    print("\nSetup complete! Update your .env file with:")
    print("DATABASE_URL=postgresql+asyncpg://read_only_user:deepagent@localhost:5432/company_db")
