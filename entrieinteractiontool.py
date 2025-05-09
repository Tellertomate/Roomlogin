#!/usr/bin/env python3
import mysql.connector
import sys
import time

# Import RFID modules (if available)
try:
    from mfrc522 import SimpleMFRC522
    import RPi.GPIO as GPIO
except ImportError:
    SimpleMFRC522 = None

# Master database configuration
master_config = {
    'host': '172.18.0.2',
    'user': 'adminuser',
    'password': 'YOURPASSWORD',
    'database': 'master'
}

def connect_master():
    try:
        conn = mysql.connector.connect(**master_config)
        if conn.is_connected():
            return conn
    except mysql.connector.Error as err:
        print("Error connecting to master database:", err)
        sys.exit(1)

def scan_chip():
    """Scan an RFID chip and return the value as a string.
       If RFID is not available, a manual entry is made."""
    if SimpleMFRC522:
        reader = SimpleMFRC522()
        try:
            print("Please place the RFID chip on the reader...")
            val, _ = reader.read() # Blocking call
            return str(val)
        finally:
            GPIO.cleanup()
    else:
        return input("RFID module not available. Enter chid manually: ")

# ------------------------------
# General search function for UPDATE/DELETE (searches in all relevant columns)
def generic_entry_search(conn, table, columns):
    """
    Searches in the specified table in all specified columns using CONCAT.
    table: Table name (e.g. students)
    columns: Liste der Spalten, z.B. ["stid", "firstname", "secondname"]
    """
    cursor = conn.cursor(dictionary=True)
    search_term = input("Enter search term (will be compared against all relevant fields): ").strip()
    like_term = f"%{search_term}%"
    # CONCAT of the columns with spaces in between
    concat_expr = "CONCAT(" + ", ' ', ".join(columns) + ")"
    query = f"SELECT * FROM {table} WHERE {concat_expr} LIKE %s"
    cursor.execute(query, (like_term,))
    results = cursor.fetchall()
    if results:
        print("Entries found:")
        for idx, row in enumerate(results):
            print(f"{idx+1}: {row}")
    else:
        print("No matching entries found.")
    cursor.close()
    return results

# ------------------------------
# CRUD for students
def create_student(conn):
    first = input("Enter student's first name: ")
    second = input("Enter student's last name: ")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO students (firstname, secondname) VALUES (%s, %s)", (first, second))
        conn.commit()
        print("Student created successfully. New student ID:", cursor.lastrowid)
    except mysql.connector.Error as err:
        print("Error creating student:", err)
        conn.rollback()
    cursor.close()

def update_student(conn):
    entries = generic_entry_search(conn, "students", ["stid", "firstname", "secondname"])
    if not entries:
        return
    try:
        sel = int(input("Select the entry to update (number): "))
        if sel < 1 or sel > len(entries):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input.")
        return
    selected = entries[sel-1]
    new_first = input(f"New first name (leave blank to keep '{selected['firstname']}'): ") or selected['firstname']
    new_second = input(f"New last name (leave blank to keep '{selected['secondname']}'): ") or selected['secondname']
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE students SET firstname = %s, secondname = %s WHERE stid = %s", 
                       (new_first, new_second, selected['stid']))
        conn.commit()
        print("Student updated successfully.")
    except mysql.connector.Error as err:
        print("Error updating student:", err)
        conn.rollback()
    cursor.close()

def delete_student(conn):
    entries = generic_entry_search(conn, "students", ["stid", "firstname", "secondname"])
    if not entries:
        return
    try:
        sel = int(input("Select the entry to delete (number): "))
        if sel < 1 or sel > len(entries):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input.")
        return
    selected = entries[sel-1]
    confirm = input(f"Confirm deletion of student {selected['firstname']} {selected['secondname']} (ID: {selected['stid']})? (y/n): ")
    if confirm.lower() != "y":
        print("Deletion canceled.")
        return
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM students WHERE stid = %s", (selected['stid'],))
        conn.commit()
        print("Student deleted successfully.")
    except mysql.connector.Error as err:
        print("Error deleting student:", err)
        conn.rollback()
    cursor.close()

# ------------------------------
# CRUD for chips
def create_chip(conn):
    chid = scan_chip()
    first = input("Enter first name for chip owner: ")
    second = input("Enter last name for chip owner: ")
    class_value = input("Enter class: ")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO chips (chid, firstname, secondname, class) VALUES (%s, %s, %s, %s)",
                       (chid, first, second, class_value))
        conn.commit()
        print(f"Chip created successfully. CHID: {chid}")
    except mysql.connector.Error as err:
        print("Error creating chip:", err)
        conn.rollback()
    cursor.close()

def update_chip(conn):
    # Scan chip to update
    print("Scan the chip you want to update:")
    chid = scan_chip()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT chid, firstname, secondname, class FROM chips WHERE chid = %s", (chid,))
    entry = cursor.fetchone()
    if not entry:
        print("No chip with that CHID found.")
        cursor.close()
        return
    print(f"Found chip: {entry}")
    print("What do you want to update?")
    print("1: First name")
    print("2: Last name")
    print("3: Class")
    try:
        sel = int(input("Select option (1/2/3): "))
    except ValueError:
        print("Invalid input.")
        cursor.close()
        return
    field_map = {1: "firstname", 2: "secondname", 3: "class"}
    if sel not in field_map:
        print("Invalid selection.")
        cursor.close()
        return
    new_value = input(f"Enter new value for {field_map[sel]}: ")
    cursor.close()
    cursor = conn.cursor()
    try:
        cursor.execute(f"UPDATE chips SET {field_map[sel]} = %s WHERE chid = %s", (new_value, chid))
        conn.commit()
        print("Chip updated successfully.")
    except mysql.connector.Error as err:
        print("Error updating chip:", err)
        conn.rollback()
    cursor.close()

def delete_chip(conn):
    print("Scan the chip you want to delete:")
    chid = scan_chip()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT chid, firstname, secondname, class FROM chips WHERE chid = %s", (chid,))
    entry = cursor.fetchone()
    if not entry:
        print("No chip with that CHID found.")
        cursor.close()
        return
    print(f"Found chip: {entry}")
    confirm = input(f"Confirm deletion of chip {chid}? (y/n): ")
    if confirm.lower() != "y":
        print("Deletion canceled.")
        cursor.close()
        return
    cursor.close()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM chips WHERE chid = %s", (chid,))
        conn.commit()
        print("Chip deleted successfully.")
    except mysql.connector.Error as err:
        print("Error deleting chip:", err)
        conn.rollback()
    cursor.close()

# ------------------------------
# CRUD for rooms
def create_room(conn):
    name = input("Enter room name: ")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO rooms (name) VALUES (%s)", (name,))
        conn.commit()
        print("Room created successfully. New room ID:", cursor.lastrowid)
    except mysql.connector.Error as err:
        print("Error creating room:", err)
        conn.rollback()
    cursor.close()

def update_room(conn):
    entries = generic_entry_search(conn, "rooms", ["roomid", "name"])
    if not entries:
        return
    try:
        sel = int(input("Select the room to update (number): "))
        if sel < 1 or sel > len(entries):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input.")
        return
    selected = entries[sel-1]
    new_name = input(f"Enter new room name (leave blank to keep '{selected['name']}'): ") or selected['name']
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE rooms SET name = %s WHERE roomid = %s", (new_name, selected['roomid']))
        conn.commit()
        print("Room updated successfully.")
    except mysql.connector.Error as err:
        print("Error updating room:", err)
        conn.rollback()
    cursor.close()

def delete_room(conn):
    entries = generic_entry_search(conn, "rooms", ["roomid", "name"])
    if not entries:
        return
    try:
        sel = int(input("Select the room to delete (number): "))
        if sel < 1 or sel > len(entries):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input.")
        return
    selected = entries[sel-1]
    confirm = input(f"Confirm deletion of room '{selected['name']}' (ID: {selected['roomid']})? (y/n): ")
    if confirm.lower() != "y":
        print("Deletion canceled.")
        return
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM rooms WHERE roomid = %s", (selected['roomid'],))
        conn.commit()
        print("Room deleted successfully.")
    except mysql.connector.Error as err:
        print("Error deleting room:", err)
        conn.rollback()
    cursor.close()

# ------------------------------
# CRUD for assignments
def create_assignments(conn):
    # Auswahl des Studenten über generic search (sucht in students)
    print("Select a student for the new assignments:")
    students = generic_entry_search(conn, "students", ["stid", "firstname", "secondname"])
    if not students:
        return
    try:
        sel = int(input("Select a student (number): "))
        if sel < 1 or sel > len(students):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input.")
        return
    selected_student = students[sel-1]
    # Scan the new Chip (chid)
    print("Scan the new chip for the assignments entry:")
    new_chid = scan_chip()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO assignments (stid, chid) VALUES (%s, %s)",
                       (selected_student['stid'], new_chid))
        conn.commit()
        print(f"assignments created successfully with student ID {selected_student['stid']} and chid {new_chid}.")
    except mysql.connector.Error as err:
        print("Error creating assignments:", err)
        conn.rollback()
    cursor.close()

def update_assignments(conn):
    print("What do you want to update in assignments?")
    print("1: Change student (name)")
    print("2: Change chip")
    try:
        sel = int(input("Select option (1/2): "))
    except ValueError:
        print("Invalid input.")
        return
    cursor = conn.cursor(dictionary=True)
    if sel == 1:
        # Change the student: First scan the associated chip to identify the entry.
        print("Scan the chip (chid) to identify the assignments entry:")
        target_chid = scan_chip()
        cursor.execute("SELECT oid, stid, chid FROM assignments WHERE chid = %s", (target_chid,))
        entry = cursor.fetchone()
        if not entry:
            print("No assignments entry found with that chid.")
            cursor.close()
            return
        print(f"Found entry: {entry}")
        print("Select new student for this entry:")
        students = generic_entry_search(conn, "students", ["stid", "firstname", "secondname"])
        if not students:
            cursor.close()
            return
        try:
            ssel = int(input("Select a student (number): "))
            if ssel < 1 or ssel > len(students):
                print("Invalid selection.")
                cursor.close()
                return
        except ValueError:
            print("Invalid input.")
            cursor.close()
            return
        new_student = students[ssel-1]
        cursor.close()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE assignments SET stid = %s WHERE oid = %s", (new_student['stid'], entry['oid']))
            conn.commit()
            print("assignments updated successfully (student changed).")
        except mysql.connector.Error as err:
            print("Error updating assignments:", err)
            conn.rollback()
        cursor.close()
    elif sel == 2:
        # Changing the chip: First select a student (using generic search) and then change the chip.
        print("Select a student for which to update the chip in assignments:")
        students = generic_entry_search(conn, "students", ["stid", "firstname", "secondname"])
        if not students:
            cursor.close()
            return
        try:
            ssel = int(input("Select a student (number): "))
            if ssel < 1 or ssel > len(students):
                print("Invalid selection.")
                cursor.close()
                return
        except ValueError:
            print("Invalid input.")
            cursor.close()
            return
        selected_student = students[ssel-1]
        cursor.execute("SELECT oid, stid, chid FROM assignments WHERE stid = %s", (selected_student['stid'],))
        entry = cursor.fetchone()
        if not entry:
            print("No assignments entry found for that student.")
            cursor.close()
            return
        print(f"Found entry: {entry}")
        print("Please scan the new chip:")
        new_chid = scan_chip()
        cursor.close()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE assignments SET chid = %s WHERE oid = %s", (new_chid, entry['oid']))
            conn.commit()
            print("assignments updated successfully (chip changed).")
        except mysql.connector.Error as err:
            print("Error updating assignments:", err)
            conn.rollback()
        cursor.close()
    else:
        print("Invalid selection.")
        cursor.close()

def delete_assignments(conn):
    entries = generic_entry_search(conn, "assignments", ["oid", "stid", "chid"])
    if not entries:
        return
    try:
        sel = int(input("Select the assignments entry to delete (number): "))
        if sel < 1 or sel > len(entries):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input.")
        return
    selected = entries[sel-1]
    confirm = input(f"Confirm deletion of assignments entry with oid {selected['oid']}? (y/n): ")
    if confirm.lower() != 'y':
        print("Deletion canceled.")
        return
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM assignments WHERE oid = %s", (selected['oid'],))
        conn.commit()
        print("assignments entry deleted successfully.")
    except mysql.connector.Error as err:
        print("Error deleting assignments:", err)
        conn.rollback()
    cursor.close()

# ------------------------------
# Generic Search for FIND mode
def generic_search(conn):
    cursor = conn.cursor(dictionary=True)
    table = input("Enter table name to search (students, chips, rooms, assignments): ").strip()
    term = input("Enter search term: ").strip()
    like_term = f"%{term}%"
    # Here we simply search in all columns: We use CONCAT of all known columns depending on the table.
    if table == "students":
        concat_expr = "CONCAT(stid, ' ', firstname, ' ', secondname)"
    elif table == "chips":
        concat_expr = "CONCAT(chid, ' ', firstname, ' ', secondname, ' ', class)"
    elif table == "rooms":
        concat_expr = "CONCAT(roomid, ' ', name)"
    elif table == "assignments":
        concat_expr = "CONCAT(oid, ' ', stid, ' ', chid)"
    else:
        print("Unknown table.")
        cursor.close()
        return
    query = f"SELECT * FROM {table} WHERE {concat_expr} LIKE %s"
    cursor.execute(query, (like_term,))
    results = cursor.fetchall()
    if results:
        print("\nResults:")
        for row in results:
            print(row)
    else:
        print("No matching entries found.")
    cursor.close()

# ------------------------------
# Main Menu (Number input)
def main():
    conn = connect_master()
    if not conn:
        sys.exit(1)
    print("=== Master Database Management ===")
    print("Select mode:")
    print("1: Change entries")
    print("2: Find entries")
    mode = input("Enter 1 or 2: ").strip()
    if mode == "1":
        print("\nSelect operation:")
        print("1: Create")
        print("2: Change")
        print("3: Delete")
        op = input("Enter 1, 2 or 3: ").strip()
        print("Select table:")
        print("1: Students")
        print("2: Chips")
        print("3: Rooms")
        print("4: assignments")
        table_sel = input("Enter 1, 2, 3 or 4: ").strip()
        # Map numbers zu Tabellennamen
        table_map = {"1": "students", "2": "chips", "3": "rooms", "4": "assignments"}
        if table_sel not in table_map:
            print("Invalid table selection.")
            conn.close()
            return
        table = table_map[table_sel]
        if table == "students":
            if op == "1":
                create_student(conn)
            elif op == "2":
                update_student(conn)
            elif op == "3":
                delete_student(conn)
            else:
                print("Invalid operation.")
        elif table == "chips":
            if op == "1":
                create_chip(conn)
            elif op == "2":
                update_chip(conn)
            elif op == "3":
                delete_chip(conn)
            else:
                print("Invalid operation.")
        elif table == "rooms":
            if op == "1":
                create_room(conn)
            elif op == "2":
                update_room(conn)
            elif op == "3":
                delete_room(conn)
            else:
                print("Invalid operation.")
        elif table == "assignments":
            if op == "1":
                create_assignments(conn)
            elif op == "2":
                update_assignments(conn)
            elif op == "3":
                delete_assignments(conn)
            else:
                print("Invalid operation.")
    elif mode == "2":
        generic_search(conn)
    else:
        print("Invalid mode selected.")
    conn.close()

if __name__ == "__main__":
    main()
