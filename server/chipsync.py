#!/usr/bin/env python3
import mysql.connector
from mysql.connector import Error

# Master database configuration (source)
master_config = {
    'host': '172.18.0.2',
    'user': 'adminuser',
    'password': 'YOURPASSWORD',
    'database': 'master'
}

# Roomregister database configuration (goal)
roomregister_config = {
    'host': '172.19.0.2',
    'user': 'adminuser',
    'password': 'YOURPASSWORD',
    'database': 'roomregister'
}

def get_master_chids():
    """
    Reads all 'chid' values from the 'chips' table in the master database.
    """
    try:
        db_master = mysql.connector.connect(**master_config)
        cursor = db_master.cursor()
        cursor.execute("SELECT chid FROM chips")
        data = cursor.fetchall()  # [(chid1,), (chid2,), ...]
        cursor.close()
        db_master.close()
        return [row[0] for row in data]
    except Error as err:
        print("Error when retrieving the master chids:", err)
        return []

def sync_roomregister_chips(master_chids):
    """
    Compares the 'chid' values read from the master database
    with those in the room register database and only inserts new entries.
    """
    try:
        db_target = mysql.connector.connect(**roomregister_config)
        cursor = db_target.cursor()
        
        # Retrieve current chids in roomregister.chips
        cursor.execute("SELECT chid FROM chips")
        existing = {row[0] for row in cursor.fetchall()}
        
        # Determine new entries: only those from master that do not yet exist.
        new_entries = [chid for chid in master_chids if chid not in existing]
        
        for chid in new_entries:
            cursor.execute("INSERT INTO chips (chid) VALUES (%s)", (chid,))
        
        db_target.commit()
        print(f"{len(new_entries)} new 'chid' values have been added to roomregister.chips.")
        cursor.close()
        db_target.close()
    except Error as err:
        print("Error during synchronization of the room register chips:", err)

def main():
    master_chids = get_master_chids()
    if master_chids:
        sync_roomregister_chips(master_chids)
    else:
        print("No data found in the master database.")

if __name__ == "__main__":
    main()
