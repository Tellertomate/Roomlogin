#!/usr/bin/env python3
import time
import signal
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import mysql.connector
from mysql.connector import Error

# Flag to control the reading process
continue_reading = True

# Global variable for saving the last CHID logged in
last_logged_chid = None

def end_read(signal, frame):
    global continue_reading
    print("Ctrl+C pressed - reading process is terminated.")
    continue_reading = False
    GPIO.cleanup()

signal.signal(signal.SIGINT, end_read)

# Initialize the RFID reader
reader = SimpleMFRC522()

# Database configuration for the Roomregister database
db_config = {
    'host': '172.19.0.2',
    'user': 'adminuser',
    'password': 'YOURPASSWORD',
    'database': 'roomregister'
}

def connect_to_database():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            return connection
    except Error as e:
        print("Error connecting to the database:", e)
    return None

def is_chip_allowed(chid, cursor):
    """
    Checks whether the scanned chip ID (chid) is present in the 'chips' table.
    """
    query = "SELECT chid FROM chips WHERE chid = %s"
    cursor.execute(query, (chid,))
    result = cursor.fetchone()
    return result is not None

def insert_into_login(chid, roomid, cursor, db):
    """
    Inserts a new login entry in the 'login' table,
    unless the same CHID logs in directly one after the other.
    The columns chid, roomid and the current timestamp (NOW()) are saved.
    """
    global last_logged_chid
    if chid == last_logged_chid:
        print(f"Chip ID {chid} was last logged in. Multiple direct logins are not permitted.")
        return

    sql = "INSERT INTO login (chid, roomid, time) VALUES (%s, %s, NOW())"
    values = (chid, roomid)
    try:
        cursor.execute(sql, values)
        db.commit()
        last_logged_chid = chid  # Update the last CHID logged in
        print(f"Entry successful: CHID {chid} - Raum {roomid}")
    except mysql.connector.Error as err:
        print("Database error:", err)
        db.rollback()

# Exemplary room (constant or defined via configuration)
roomid = 1

print("RFID reader active - please insert the RFID chip.")

db = connect_to_database()
if db:
    cursor = db.cursor()
    while continue_reading:
        try:
            # Checks whether a card is present (non-blocking)
            chipid, text = reader.read_no_block()
            if chipid:
                # Convert the read number into a string if necessary
                chid = str(chipid)
                print("Gelesene Chip-ID:", chid)
                # Check whether the CHID exists in the chips table
                if is_chip_allowed(chid, cursor):
                    insert_into_login(chid, roomid, cursor, db)
                else:
                    print(f"Chip ID {chid} is not in the allowed list.")
                print("Please wait 2 seconds before reading the next card...")
                time.sleep(2)
            else:
                time.sleep(0.1)  # Reduce CPU utilization
        except Exception as e:
            print("Reading error:", e)
            GPIO.cleanup()
            break
    cursor.close()
    db.close()
else:
    print("Database connection could not be established.")
