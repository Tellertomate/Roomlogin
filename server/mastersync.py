#!/usr/bin/env python3
import mysql.connector
from mysql.connector import Error

# Konfiguration der Roomregister-Datenbank (Quelle)
roomregister_config = {
    'host': 'localhost',
    'user': 'user',
    'password': 'HimbeerKuchen!',
    'database': 'roomregister'
}

# Konfiguration der Master-Datenbank (Ziel)
master_config = {
    'host': '172.18.0.2',
    'user': 'user',
    'password': 'HimbeerKuchen!',
    'database': 'master'
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
    Ermittelt den letzten (maximalen) Zeitstempel aus der Master-Tabelle,
    in die bereits Login-Einträge übertragen wurden.
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
    Liest neue Login-Einträge aus der Roomregister-Login-Tabelle.
    Annahme: Die Tabelle "login" enthält die Spalten: chid, roomid, time.
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
    Sucht in der Master-Zuordnungstabelle (zuordnung) anhand der CHID nach der zugehörigen OID.
    Annahme: Die Tabelle "zuordnung" enthält die Spalten: oid und chid.
    """
    try:
        cursor = master_db.cursor()
        cursor.execute("SELECT oid FROM zuordnung WHERE chid = %s", (chid,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None
    except Error as err:
        print("Error fetching OID for CHID", chid, ":", err)
        return None

def insert_into_master(master_db, oid, roomid, time):
    """
    Fügt in der Master-Tabelle (master) einen neuen Eintrag ein.
    Angenommen: Spalten in master sind oid, roomid und time.
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
        print("Datenbankverbindung fehlgeschlagen.")
        return

    last_transfer_time = fetch_last_transfer_time(master_db)
    print("Letzter Transfer-Zeitstempel:", last_transfer_time)

    new_logins = fetch_new_logins(room_db, last_transfer_time)
    print(f"Neue Login-Einträge gefunden: {len(new_logins)}")

    inserted_count = 0

    for entry in new_logins:
        chid = entry['chid']
        roomid = entry['roomid']
        time = entry['time']
        oid = get_oid_for_chid(master_db, chid)
        if oid:
            # Eintrag in master.master einfügen
            if insert_into_master(master_db, oid, roomid, time):
                inserted_count += 1
        else:
            print(f"Kein OID-Mapping für CHID {chid} gefunden in zuordnung.")

    print(f"Insgesamt wurden {inserted_count} neue Einträge in master.master eingefügt.")

    room_db.close()
    master_db.close()

if __name__ == "__main__":
    main()
