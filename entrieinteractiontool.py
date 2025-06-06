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

def get_valid_int(prompt, min_val=None, max_val=None):
    """Fragt den Nutzer nach einer Ganzzahl und prüft die Eingabe."""
    while True:
        try:
            val = int(input(prompt))
            if (min_val is not None and val < min_val) or (max_val is not None and val > max_val):
                print(f"Bitte eine Zahl zwischen {min_val} und {max_val} eingeben.")
                continue
            return val
        except ValueError:
            print("Ungültige Eingabe. Bitte eine Zahl eingeben.")

def confirm_action(prompt):
    """Ask the user for confirmation (y/n)."""
    while True:
        val = input(f"{prompt} (y/n): ").strip().lower()
        if val == 'y':
            return True
        elif val == 'n':
            return False
        else:
            print("Please enter 'y' or 'n'.")

# ------------------------------
# General search function for UPDATE/DELETE (searches in all relevant columns)
def generic_entry_search(conn, table, columns):
    """
    Searches in the specified table in all specified columns using CONCAT.
    table: Table name (e.g. students)
    columns: List of columns, e.g. ["stid", "firstname", "secondname"]
    """
    cursor = conn.cursor(dictionary=True)
    search_term = input("Enter search term (will be compared against all relevant fields): ").strip()
    if not search_term:
        print("Search term cannot be empty.")
        return []
    like_term = f"%{search_term}%"
    concat_expr = "CONCAT(" + ", ' ', ".join(columns) + ")"
    query = f"SELECT * FROM {table} WHERE {concat_expr} LIKE %s"
    try:
        cursor.execute(query, (like_term,))
        results = cursor.fetchall()
    except mysql.connector.Error as err:
        print("Error during search:", err)
        results = []
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
    sel = get_valid_int("Select the entry to update (number): ", 1, len(entries))
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
    sel = get_valid_int("Select the entry to delete (number): ", 1, len(entries))
    selected = entries[sel-1]
    if not confirm_action(f"Confirm deletion of student {selected['firstname']} {selected['secondname']} (ID: {selected['stid']})?"):
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
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO chips (chid) VALUES (%s)", (chid,))
        conn.commit()
        print(f"Chip created successfully. CHID: {chid}")
    except mysql.connector.Error as err:
        print("Error creating chip:", err)
        conn.rollback()
    cursor.close()

def update_chip(conn):
    print("Scan the chip you want to update:")
    chid = scan_chip()
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT chid, firstname, secondname, class FROM chips WHERE chid = %s", (chid,))
        entry = cursor.fetchone()
        if not entry:
            print("No chip with that CHID found.")
            return
        print(f"Found chip: {entry}")
        print("What do you want to update?")
        print("1: First name")
        print("2: Last name")
        print("3: Class")
        sel = get_valid_int("Select option (1/2/3): ", 1, 3)
        field_map = {1: "firstname", 2: "secondname", 3: "class"}
        new_value = input(f"Enter new value for {field_map[sel]}: ")
    with conn.cursor() as cursor:
        try:
            cursor.execute(f"UPDATE chips SET {field_map[sel]} = %s WHERE chid = %s", (new_value, chid))
            conn.commit()
            print("Chip updated successfully.")
        except mysql.connector.Error as err:
            print("Error updating chip:", err)
            conn.rollback()

def delete_chip(conn):
    print("Scan the chip you want to delete:")
    chid = scan_chip()
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT chid, firstname, secondname, class FROM chips WHERE chid = %s", (chid,))
        entry = cursor.fetchone()
        if not entry:
            print("No chip with that CHID found.")
            return
        print(f"Found chip: {entry}")
        if not confirm_action(f"Confirm deletion of chip {chid}?"):
            print("Deletion canceled.")
            return
    with conn.cursor() as cursor:
        try:
            cursor.execute("DELETE FROM chips WHERE chid = %s", (chid,))
            conn.commit()
            print("Chip deleted successfully.")
        except mysql.connector.Error as err:
            print("Error deleting chip:", err)
            conn.rollback()

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
    sel = get_valid_int("Select the room to update (number): ", 1, len(entries))
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
    sel = get_valid_int("Select the room to delete (number): ", 1, len(entries))
    selected = entries[sel-1]
    if not confirm_action(f"Confirm deletion of room '{selected['name']}' (ID: {selected['roomid']})?"):
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
    print("Select a student for the new assignments:")
    students = generic_entry_search(conn, "students", ["stid", "firstname", "secondname"])
    if not students:
        return
    sel = get_valid_int("Select a student (number): ", 1, len(students))
    selected_student = students[sel-1]
    print("Scan the new chip for the assignments entry:")
    new_chid = scan_chip()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO assignments (stid, chid) VALUES (%s, %s)",
                       (selected_student['stid'], new_chid))
        conn.commit()
        print(f"Assignments created successfully with student ID {selected_student['stid']} and chip ID {new_chid}.")
    except mysql.connector.Error as err:
        print("Error creating assignments:", err)
        conn.rollback()
    cursor.close()

def update_assignments(conn):
    print("What do you want to update in assignments?")
    print("1: Change student (name)")
    print("2: Change chip")
    sel = get_valid_int("Select option (1/2): ", 1, 2)
    with conn.cursor(dictionary=True) as cursor:
        if sel == 1:
            print("Scan the chip (chip ID) to identify the assignments entry:")
            target_chid = scan_chip()
            cursor.execute("SELECT oid, stid, chid FROM assignments WHERE chid = %s", (target_chid,))
            entry = cursor.fetchone()
            if not entry:
                print("No assignments entry found with that chip ID.")
                return
            print(f"Found entry: {entry}")
            print("Select new student for this entry:")
            students = generic_entry_search(conn, "students", ["stid", "firstname", "secondname"])
            if not students:
                return
            ssel = get_valid_int("Select a student (number): ", 1, len(students))
            new_student = students[ssel-1]
            with conn.cursor() as cur2:
                try:
                    cur2.execute("UPDATE assignments SET stid = %s WHERE oid = %s", (new_student['stid'], entry['oid']))
                    conn.commit()
                    print("Assignments updated successfully (student changed).")
                except mysql.connector.Error as err:
                    print("Error updating assignments:", err)
                    conn.rollback()
        elif sel == 2:
            print("Select a student for which to update the chip in assignments:")
            students = generic_entry_search(conn, "students", ["stid", "firstname", "secondname"])
            if not students:
                return
            ssel = get_valid_int("Select a student (number): ", 1, len(students))
            selected_student = students[ssel-1]
            cursor.execute("SELECT oid, stid, chid FROM assignments WHERE stid = %s", (selected_student['stid'],))
            entry = cursor.fetchone()
            if not entry:
                print("No assignments entry found for that student.")
                return
            print(f"Found entry: {entry}")
            print("Please scan the new chip:")
            new_chid = scan_chip()
            with conn.cursor() as cur2:
                try:
                    cur2.execute("UPDATE assignments SET chid = %s WHERE oid = %s", (new_chid, entry['oid']))
                    conn.commit()
                    print("Assignments updated successfully (chip changed).")
                except mysql.connector.Error as err:
                    print("Error updating assignments:", err)
                    conn.rollback()

def delete_assignments(conn):
    entries = generic_entry_search(conn, "assignments", ["oid", "stid", "chid"])
    if not entries:
        return
    sel = get_valid_int("Select the assignments entry to delete (number): ", 1, len(entries))
    selected = entries[sel-1]
    if not confirm_action(f"Confirm deletion of assignments entry with oid {selected['oid']}?"):
        print("Deletion canceled.")
        return
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM assignments WHERE oid = %s", (selected['oid'],))
        conn.commit()
        print("Assignments entry deleted successfully.")
    except mysql.connector.Error as err:
        print("Error deleting assignments:", err)
        conn.rollback()
    cursor.close()

# ------------------------------
# Generic Search for FIND mode
def generic_search(conn):
    cursor = conn.cursor(dictionary=True)
    table = input("Enter table name to search (students, chips, rooms, assignments): ").strip()
    if table not in ("students", "chips", "rooms", "assignments"):
        print("Unknown table.")
        cursor.close()
        return
    term = input("Enter search term: ").strip()
    if not term:
        print("Search term cannot be empty.")
        cursor.close()
        return
    like_term = f"%{term}%"
    if table == "students":
        concat_expr = "CONCAT(stid, ' ', firstname, ' ', secondname)"
    elif table == "chips":
        concat_expr = "CONCAT(chid, ' ', firstname, ' ', secondname, ' ', class)"
    elif table == "rooms":
        concat_expr = "CONCAT(roomid, ' ', name)"
    elif table == "assignments":
        concat_expr = "CONCAT(oid, ' ', stid, ' ', chid)"
    query = f"SELECT * FROM {table} WHERE {concat_expr} LIKE %s"
    try:
        cursor.execute(query, (like_term,))
        results = cursor.fetchall()
    except mysql.connector.Error as err:
        print("Error during search:", err)
        results = []
    if results:
        print("\nResults:")
        for row in results:
            print(row)
    else:
        print("No matching entries found.")
    cursor.close()

# ------------------------------
# Erweiterte Suche in der master-Tabelle
def search_master(conn):
    print("\n--- Advanced search in the master table ---")
    print("You can filter by any criteria. Leave fields empty to ignore them.")
    schueler_name = input("Student first or last name (optional): ").strip()
    chip_id = input("Chip ID (optional): ").strip()
    room_name = input("Room name (optional): ").strip()
    room_id = input("Room ID (optional): ").strip()
    date_exact = input("Exact date (YYYY-MM-DD, optional): ").strip()
    date_from = input("From date (YYYY-MM-DD, optional): ").strip()
    date_to = input("To date (YYYY-MM-DD, optional): ").strip()

    query = '''
        SELECT m.oid, m.roomid, r.name AS roomname, m.time, s.stid, s.firstname, s.secondname, c.chid
        FROM master m
        JOIN assignments a ON m.oid = a.oid
        JOIN students s ON a.stid = s.stid
        JOIN chips c ON a.chid = c.chid
        JOIN rooms r ON m.roomid = r.roomid
        WHERE 1=1
    '''
    params = []
    if schueler_name:
        query += " AND (s.firstname LIKE %s OR s.secondname LIKE %s)"
        like = f"%{schueler_name}%"
        params.extend([like, like])
    if chip_id:
        query += " AND c.chid = %s"
        params.append(chip_id)
    if room_name:
        query += " AND r.name LIKE %s"
        params.append(f"%{room_name}%")
    if room_id:
        query += " AND m.roomid = %s"
        params.append(room_id)
    if date_exact:
        query += " AND DATE(m.time) = %s"
        params.append(date_exact)
    if date_from:
        query += " AND DATE(m.time) >= %s"
        params.append(date_from)
    if date_to:
        query += " AND DATE(m.time) <= %s"
        params.append(date_to)
    query += " ORDER BY m.time DESC"

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
    except mysql.connector.Error as err:
        print("Error during search:", err)
        results = []
    if results:
        print(f"\nEntries found: {len(results)}")
        for row in results:
            print(f"Date: {row['time']} | Room: {row['roomname']} (ID: {row['roomid']}) | Student: {row['firstname']} {row['secondname']} (ID: {row['stid']}) | Chip: {row['chid']} | OID: {row['oid']}")
    else:
        print("No matching entries found.")
    cursor.close()

# ------------------------------
# Main Menu (Number input)
def main():
    conn = connect_master()
    if not conn:
        sys.exit(1)
    while True:
        print("=== Master Database Management ===")
        print("Select mode:")
        print("1: Change entries")
        print("2: Find entries")
        print("3: Advanced search in master")
        print("0: Exit")
        mode = input("Enter 1, 2, 3 or 0: ").strip()
        if mode == "0":
            break
        elif mode == "1":
            print("\nSelect operation:")
            print("1: Create")
            print("2: Change")
            print("3: Delete")
            op = input("Enter 1, 2 or 3: ").strip()
            print("Select table:")
            print("1: Students")
            print("2: Chips")
            print("3: Rooms")
            print("4: Assignments")
            table_sel = input("Enter 1, 2, 3 or 4: ").strip()
            table_map = {"1": "students", "2": "chips", "3": "rooms", "4": "assignments"}
            if table_sel not in table_map:
                print("Invalid table selection.")
                continue
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
        elif mode == "3":
            search_master(conn)
        else:
            print("Invalid mode selected.")
    conn.close()

if __name__ == "__main__":
    main()
