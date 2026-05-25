"""
Script to add a complex table to the PostgreSQL database for testing.
This table includes multiple relationships, various data types, and complex scenarios.
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def add_complex_table():
    """Add a complex table with multiple relationships and data types."""
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="deepagent",  # Change this to your PostgreSQL password
        database="company_db"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    print("Adding complex tables for testing...")

    # Create employees table (self-referencing relationship)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id SERIAL PRIMARY KEY,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        phone VARCHAR(20),
        hire_date DATE NOT NULL,
        job_title VARCHAR(100),
        salary DECIMAL(12, 2),
        commission_pct DECIMAL(5, 2),
        manager_id INTEGER REFERENCES employees(employee_id),
        department_id INTEGER,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("✓ Created employees table")

    # Create departments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        department_id SERIAL PRIMARY KEY,
        department_name VARCHAR(100) NOT NULL,
        location_id INTEGER,
        manager_id INTEGER REFERENCES employees(employee_id),
        budget DECIMAL(15, 2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("✓ Created departments table")

    # Add foreign key to employees
    cursor.execute("""
    ALTER TABLE employees 
    ADD CONSTRAINT fk_department 
    FOREIGN KEY (department_id) 
    REFERENCES departments(department_id);
    """)
    print("✓ Added department foreign key to employees")

    # Create locations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        location_id SERIAL PRIMARY KEY,
        street_address VARCHAR(255),
        postal_code VARCHAR(20),
        city VARCHAR(100) NOT NULL,
        state_province VARCHAR(100),
        country_id CHAR(2) NOT NULL
    );
    """)
    print("✓ Created locations table")

    # Add foreign key to departments
    cursor.execute("""
    ALTER TABLE departments 
    ADD CONSTRAINT fk_location 
    FOREIGN KEY (location_id) 
    REFERENCES locations(location_id);
    """)
    print("✓ Added location foreign key to departments")

    # Create projects table (many-to-many with employees)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        project_id SERIAL PRIMARY KEY,
        project_name VARCHAR(200) NOT NULL,
        description TEXT,
        start_date DATE,
        end_date DATE,
        budget DECIMAL(15, 2),
        status VARCHAR(20) DEFAULT 'PLANNING' CHECK (status IN ('PLANNING', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD', 'CANCELLED')),
        department_id INTEGER REFERENCES departments(department_id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("✓ Created projects table")

    # Create project_assignments (junction table for many-to-many)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_assignments (
        assignment_id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES employees(employee_id),
        project_id INTEGER REFERENCES projects(project_id),
        role VARCHAR(100),
        hours_allocated INTEGER,
        start_date DATE,
        end_date DATE,
        UNIQUE(employee_id, project_id)
    );
    """)
    print("✓ Created project_assignments table")

    # Create performance_reviews table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS performance_reviews (
        review_id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES employees(employee_id),
        reviewer_id INTEGER REFERENCES employees(employee_id),
        review_date DATE NOT NULL,
        rating INTEGER CHECK (rating BETWEEN 1 AND 5),
        comments TEXT,
        goals_next_period TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print("✓ Created performance_reviews table")

    # Create salary_history table (temporal data)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS salary_history (
        history_id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES employees(employee_id),
        old_salary DECIMAL(12, 2),
        new_salary DECIMAL(12, 2),
        change_date DATE NOT NULL,
        change_reason VARCHAR(200),
        approved_by INTEGER REFERENCES employees(employee_id)
    );
    """)
    print("✓ Created salary_history table")

    # Insert sample data for locations
    cursor.execute("""
    INSERT INTO locations (street_address, postal_code, city, state_province, country_id) VALUES
    ('123 Main St', '110001', 'Delhi', 'Delhi', 'IN'),
    ('456 Tech Park', '400001', 'Mumbai', 'Maharashtra', 'IN'),
    ('789 IT Corridor', '560001', 'Bangalore', 'Karnataka', 'IN'),
    ('321 Business Ave', '600001', 'Chennai', 'Tamil Nadu', 'IN'),
    ('654 Innovation Blvd', '500001', 'Hyderabad', 'Telangana', 'IN');
    """)
    print("✓ Inserted locations data")

    # Insert sample data for departments
    cursor.execute("""
    INSERT INTO departments (department_name, location_id, budget) VALUES
    ('Engineering', 3, 5000000.00),
    ('Sales', 1, 3000000.00),
    ('Marketing', 2, 2000000.00),
    ('Human Resources', 1, 1500000.00),
    ('Finance', 2, 2500000.00),
    ('Research & Development', 3, 4000000.00);
    """)
    print("✓ Inserted departments data")

    # Insert sample data for employees
    cursor.execute("""
    INSERT INTO employees (first_name, last_name, email, phone, hire_date, job_title, salary, commission_pct, manager_id, department_id) VALUES
    ('Rajesh', 'Kumar', 'rajesh.kumar@company.com', '+91-9876543210', '2020-01-15', 'CEO', 250000.00, NULL, NULL, 1),
    ('Priya', 'Sharma', 'priya.sharma@company.com', '+91-9876543211', '2020-02-01', 'CTO', 200000.00, NULL, 1, 1),
    ('Amit', 'Patel', 'amit.patel@company.com', '+91-9876543212', '2020-03-10', 'VP Sales', 180000.00, 0.15, 1, 2),
    ('Sneha', 'Reddy', 'sneha.reddy@company.com', '+91-9876543213', '2020-04-20', 'Senior Engineer', 120000.00, NULL, 2, 1),
    ('Vikram', 'Singh', 'vikram.singh@company.com', '+91-9876543214', '2020-05-15', 'Engineer', 90000.00, NULL, 4, 1),
    ('Anjali', 'Gupta', 'anjali.gupta@company.com', '+91-9876543215', '2020-06-01', 'Sales Manager', 100000.00, 0.10, 3, 2),
    ('Rahul', 'Verma', 'rahul.verma@company.com', '+91-9876543216', '2020-07-10', 'Sales Rep', 70000.00, 0.08, 6, 2),
    ('Neha', 'Joshi', 'neha.joshi@company.com', '+91-9876543217', '2020-08-20', 'Marketing Manager', 95000.00, NULL, 1, 3),
    ('Arun', 'Nair', 'arun.nair@company.com', '+91-9876543218', '2020-09-15', 'HR Manager', 90000.00, NULL, 1, 4),
    ('Deepa', 'Menon', 'deepa.menon@company.com', '+91-9876543219', '2020-10-01', 'Finance Manager', 110000.00, NULL, 1, 5),
    ('Karthik', 'Iyer', 'karthik.iyer@company.com', '+91-9876543220', '2021-01-10', 'Research Scientist', 130000.00, NULL, 2, 6),
    ('Meera', 'Krishnan', 'meera.krishnan@company.com', '+91-9876543221', '2021-02-15', 'Junior Engineer', 65000.00, NULL, 4, 1);
    """)
    print("✓ Inserted employees data")

    # Update department managers
    cursor.execute("""
    UPDATE departments SET manager_id = 2 WHERE department_name = 'Engineering';
    UPDATE departments SET manager_id = 3 WHERE department_name = 'Sales';
    UPDATE departments SET manager_id = 8 WHERE department_name = 'Marketing';
    UPDATE departments SET manager_id = 9 WHERE department_name = 'Human Resources';
    UPDATE departments SET manager_id = 10 WHERE department_name = 'Finance';
    UPDATE departments SET manager_id = 11 WHERE department_name = 'Research & Development';
    """)
    print("✓ Updated department managers")

    # Insert sample data for projects
    cursor.execute("""
    INSERT INTO projects (project_name, description, start_date, end_date, budget, status, department_id) VALUES
    ('Website Redesign', 'Complete overhaul of company website', '2024-01-01', '2024-06-30', 500000.00, 'IN_PROGRESS', 1),
    ('Mobile App Development', 'Build iOS and Android apps', '2024-02-01', '2024-12-31', 800000.00, 'IN_PROGRESS', 1),
    ('Q1 Sales Campaign', 'Aggressive sales push for Q1', '2024-01-15', '2024-03-31', 200000.00, 'COMPLETED', 2),
    ('Brand Awareness', 'Increase brand visibility', '2024-03-01', '2024-09-30', 300000.00, 'IN_PROGRESS', 3),
    ('Employee Training', 'Upskilling program', '2024-04-01', '2024-12-31', 150000.00, 'PLANNING', 4),
    ('AI Research Project', 'Explore AI/ML applications', '2024-01-01', '2025-12-31', 1000000.00, 'IN_PROGRESS', 6),
    ('ERP Implementation', 'New ERP system rollout', '2024-06-01', '2025-06-30', 750000.00, 'PLANNING', 5);
    """)
    print("✓ Inserted projects data")

    # Insert sample data for project_assignments
    cursor.execute("""
    INSERT INTO project_assignments (employee_id, project_id, role, hours_allocated, start_date, end_date) VALUES
    (4, 1, 'Tech Lead', 40, '2024-01-01', '2024-06-30'),
    (5, 1, 'Developer', 40, '2024-01-01', '2024-06-30'),
    (12, 1, 'Developer', 40, '2024-02-01', '2024-06-30'),
    (4, 2, 'Architect', 20, '2024-02-01', '2024-12-31'),
    (5, 2, 'Developer', 40, '2024-02-01', '2024-12-31'),
    (12, 2, 'Developer', 40, '2024-02-01', '2024-12-31'),
    (7, 3, 'Sales Rep', 40, '2024-01-15', '2024-03-31'),
    (8, 4, 'Campaign Manager', 30, '2024-03-01', '2024-09-30'),
    (9, 5, 'Training Coordinator', 20, '2024-04-01', '2024-12-31'),
    (11, 6, 'Lead Researcher', 40, '2024-01-01', '2025-12-31'),
    (10, 7, 'Finance Lead', 20, '2024-06-01', '2025-06-30');
    """)
    print("✓ Inserted project assignments data")

    # Insert sample data for performance_reviews
    cursor.execute("""
    INSERT INTO performance_reviews (employee_id, reviewer_id, review_date, rating, comments, goals_next_period) VALUES
    (4, 2, '2024-06-30', 5, 'Exceptional performance, led website redesign successfully', 'Take on more leadership responsibilities'),
    (5, 4, '2024-06-30', 4, 'Good progress, needs improvement in code reviews', 'Improve code quality and mentoring skills'),
    (6, 3, '2024-06-30', 4, 'Exceeded sales targets by 15%', 'Expand to new markets'),
    (7, 6, '2024-06-30', 3, 'Met expectations, room for growth', 'Increase client engagement'),
    (8, 1, '2024-06-30', 4, 'Successful Q1 campaign execution', 'Launch digital marketing initiatives'),
    (9, 1, '2024-06-30', 4, 'Improved employee satisfaction scores', 'Implement new training programs'),
    (10, 1, '2024-06-30', 5, 'Excellent financial management', 'Lead ERP implementation'),
    (11, 2, '2024-06-30', 5, 'Breakthrough in AI research', 'Publish research findings'),
    (12, 4, '2024-06-30', 3, 'Learning and growing', 'Complete certification');
    """)
    print("✓ Inserted performance reviews data")

    # Insert sample data for salary_history
    cursor.execute("""
    INSERT INTO salary_history (employee_id, old_salary, new_salary, change_date, change_reason, approved_by) VALUES
    (4, 100000.00, 120000.00, '2023-07-01', 'Annual promotion', 2),
    (5, 80000.00, 90000.00, '2023-07-01', 'Annual increment', 4),
    (6, 90000.00, 100000.00, '2023-07-01', 'Performance bonus', 3),
    (7, 60000.00, 70000.00, '2023-07-01', 'Annual increment', 6),
    (8, 85000.00, 95000.00, '2023-07-01', 'Annual promotion', 1),
    (9, 80000.00, 90000.00, '2023-07-01', 'Annual increment', 1),
    (10, 100000.00, 110000.00, '2023-07-01', 'Annual promotion', 1),
    (11, 120000.00, 130000.00, '2023-07-01', 'Research excellence', 2),
    (12, 60000.00, 65000.00, '2023-07-01', 'Annual increment', 4);
    """)
    print("✓ Inserted salary history data")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n✅ Complex tables added successfully!")
    print("\nNew tables created:")
    print("  - employees (with self-referencing manager relationship)")
    print("  - departments (with manager and location relationships)")
    print("  - locations")
    print("  - projects (with department relationship)")
    print("  - project_assignments (many-to-many junction table)")
    print("  - performance_reviews (with employee and reviewer relationships)")
    print("  - salary_history (temporal data with approval tracking)")
    print("\nTotal tables in database: 10")
    print("  - products, customers, orders (original)")
    print("  - employees, departments, locations, projects, project_assignments, performance_reviews, salary_history (new)")


if __name__ == "__main__":
    add_complex_table()
