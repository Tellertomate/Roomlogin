import mysql.connector

# Database connection configuration
DB_CONFIG = {
    'host': '172.19.0.2',
    'user': 'adminuser',
    'password': 'YOURPASSWORD'
}

SQL_FILE = 'room.sql'

def read_sql_file(file_path):
    """Reads the SQL file and splits it into individual statements."""
    with open(file_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    # Split statements by semicolon, ignoring empty lines
    statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
    return statements

def run_sql_statements(statements):
    """Executes each SQL statement individually."""
    try:
        print("Connecting to the database server...")
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()

        for stmt in statements:
            try:
                print(f"Executing: {stmt[:60]}...")
                cursor.execute(stmt)
            except mysql.connector.Error as e:
                print(f"Error executing statement: {e}")
        
        cnx.commit()
        cursor.close()
        cnx.close()
        print("Setup completed successfully.")
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        exit(1)

def main():
    sql_statements = read_sql_file(SQL_FILE)
    run_sql_statements(sql_statements)

if __name__ == '__main__':
    main()
