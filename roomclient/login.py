#!/usr/bin/env python3
import time
import signal
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import mysql.connector
from mysql.connector import Error

# Flag, um den Lesevorgang zu steuern
continue_reading = True

# Globale Variable zum Speichern der zuletzt eingeloggten CHID
last_logged_chid = None

def end_read(signal, frame):
    global continue_reading
    print("Ctrl+C gedrückt – Lesevorgang wird beendet.")
    continue_reading = False
    GPIO.cleanup()

signal.signal(signal.SIGINT, end_read)

# Initialisiere den RFID-Leser
reader = SimpleMFRC522()

# Datenbankkonfiguration für die Roomregister-Datenbank
db_config = {
    'host': 'localhost',
    'user': 'user',
    'password': 'HimbeerKuchen!',
    'database': 'roomregister'
}

def connect_to_database():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            return connection
    except Error as e:
        print("Fehler beim Verbinden zur Datenbank:", e)
    return None

def is_chip_allowed(chid, cursor):
    """
    Prüft, ob die gescannte Chip-ID (chid) in der Tabelle 'chips' vorhanden ist.
    """
    query = "SELECT chid FROM chips WHERE chid = %s"
    cursor.execute(query, (chid,))
    result = cursor.fetchone()
    return result is not None

def insert_into_login(chid, roomid, cursor, db):
    """
    Fügt einen neuen Login-Eintrag in die Tabelle 'login' ein,
    sofern sich nicht die gleiche CHID direkt hintereinander einloggt.
    Es werden die Spalten chid, roomid und der aktuelle Zeitstempel (NOW()) gespeichert.
    """
    global last_logged_chid
    if chid == last_logged_chid:
        print(f"Chip-ID {chid} wurde zuletzt eingeloggt. Kein mehrfaches direktes Einloggen erlaubt.")
        return

    sql = "INSERT INTO login (chid, roomid, time) VALUES (%s, %s, NOW())"
    values = (chid, roomid)
    try:
        cursor.execute(sql, values)
        db.commit()
        last_logged_chid = chid  # Aktualisiere den zuletzt eingeloggten CHID
        print(f"Eintrag erfolgreich: CHID {chid} - Raum {roomid}")
    except mysql.connector.Error as err:
        print("Datenbankfehler:", err)
        db.rollback()

# Beispielhafter Raum (konstant oder über Konfiguration festgelegt)
roomid = 1

print("RFID-Leser aktiv – bitte den RFID-Chip anlegen.")

db = connect_to_database()
if db:
    cursor = db.cursor()
    while continue_reading:
        try:
            # Überprüft, ob eine Karte vorhanden ist (nicht blockierend)
            chipid, text = reader.read_no_block()
            if chipid:
                # Konvertiere ggf. die gelesene Zahl in einen String
                chid = str(chipid)
                print("Gelesene Chip-ID:", chid)
                # Überprüfen, ob die CHID in der Chips-Tabelle existiert
                if is_chip_allowed(chid, cursor):
                    insert_into_login(chid, roomid, cursor, db)
                else:
                    print(f"Chip-ID {chid} ist nicht in der erlaubten Liste vorhanden.")
                print("Bitte 2 Sekunden warten, bevor die nächste Karte gelesen wird...")
                time.sleep(2)
            else:
                time.sleep(0.1)  # CPU-Auslastung reduzieren
        except Exception as e:
            print("Fehler beim Lesen:", e)
            GPIO.cleanup()
            break
    cursor.close()
    db.close()
else:
    print("Datenbankverbindung konnte nicht hergestellt werden.")
