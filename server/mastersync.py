#!/usr/bin/env python3
import mysql.connector
from mysql.connector import Error

# Configuration of the master database (target)
master_config = {
    'host': '172.18.0.2',
    'user': 'user',
    'password': 'YOURPASSWORD',
    'database': 'master'
}

# Configuration of the room register database (source)
roomregister_config = {
    'host': '172.19.0.2',
    'user': 'adminuser',
    'password': 'YOURPASSWORD',
    'database': 'roomregister'
}

def connect_database(config):
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            return conn
    except Error as err:
        print("Error connecting to database:", err)
    return None

def fetch_last_transfer_time(master_db):
    """
    Determines the last (maximum) timestamp from the master table,
    into which login entries have already been transferred.
    """
    try:
        cursor = master_db.cursor()
        cursor.execute("SELECT MAX(time) FROM master")
        result = cursor.fetchone()
        cursor.close()
        # Falls kein Eintrag existiert, verwenden wir einen sehr alten Zeitstempel.
        return result[0] if result[0] is not None else '1970-01-01 00:00:00'
    except Error as err:
        print("Error fetching last transfer time:", err)
        return '1970-01-01 00:00:00'

def fetch_new_logins(room_db, last_time):
    """
    Reads new login entries from the Roomregister login table.
    Assumption: The “login” table contains the columns: chid, roomid, time.
    """
    try:
        cursor = room_db.cursor(dictionary=True)
        query = "SELECT chid, roomid, time FROM login WHERE time > %s"
        cursor.execute(query, (last_time,))
        results = cursor.fetchall()
        cursor.close()
        return results
    except Error as err:
        print("Error fetching new logins:", err)
        return []

def get_oid_for_chid(master_db, chid):
    """
    Searches for the corresponding OID in the master assignment table (assignment) using the CHID.
    Assumption: The “assignment” table contains the columns: oid and chid.
    """
    try:
        cursor = master_db.cursor()
        cursor.execute("SELECT oid FROM assignments WHERE chid = %s", (chid,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None
    except Error as err:
        print("Error fetching OID for CHID", chid, ":", err)
        return None

def insert_into_master(master_db, oid, roomid, time):
    """
    Inserts a new entry in the master table (master).
    Assumed: Columns in master are oid, roomid and time.
    """
    try:
        cursor = master_db.cursor()
        query = "INSERT INTO master (oid, roomid, time) VALUES (%s, %s, %s)"
        cursor.execute(query, (oid, roomid, time))
        master_db.commit()
        cursor.close()
        return True
    except Error as err:
        print("Error inserting into master:", err)
        master_db.rollback()
        return False

def main():
    room_db = connect_database(roomregister_config)
    master_db = connect_database(master_config)

    if not room_db or not master_db:
        print("Database connection failed.")
        return

    last_transfer_time = fetch_last_transfer_time(master_db)
    print("Last transfer timestamp:", last_transfer_time)

    new_logins = fetch_new_logins(room_db, last_transfer_time)
    print(f"New login entries found: {len(new_logins)}")

    inserted_count = 0

    for entry in new_logins:
        chid = entry['chid']
        roomid = entry['roomid']
        time = entry['time']
        oid = get_oid_for_chid(master_db, chid)
        if oid:
            # Insert entry in master.master
            if insert_into_master(master_db, oid, roomid, time):
                inserted_count += 1
        else:
            print(f"No OID mapping found for CHID {chid} in mapping.")

    print(f"A total of {inserted_count} new entries were inserted in master.master.")

    room_db.close()
    master_db.close()

if __name__ == "__main__":
    main()
