#!/usr/bin/env python3
import mysql.connector
from mysql.connector import Error

# Master database configuration (Quelle)
master_config = {
    'host': '172.18.0.2',
    'user': 'user',
    'password': 'HimbeerKuchen!',
    'database': 'master'
}

# Roomregister database configuration (Ziel)
roomregister_config = {
    'host': 'localhost',
    'user': 'user',
    'password': 'HimbeerKuchen!',
    'database': 'roomregister'
}

def get_master_chids():
    """
    Liest alle 'chid'-Werte aus der Tabelle 'chips' in der Master-Datenbank.
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
        print("Fehler beim Abrufen der Master-chids:", err)
        return []

def sync_roomregister_chips(master_chids):
    """
    Vergleicht die aus der Master-Datenbank ausgelesenen 'chid'-Werte
    mit denen in der Roomregister-Datenbank und fügt nur neue Einträge ein.
    """
    try:
        db_target = mysql.connector.connect(**roomregister_config)
        cursor = db_target.cursor()
        
        # Aktuelle chids in roomregister.chips abrufen
        cursor.execute("SELECT chid FROM chips")
        existing = {row[0] for row in cursor.fetchall()}
        
        # Neue Einträge ermitteln: nur die aus master, die noch nicht vorhanden sind.
        new_entries = [chid for chid in master_chids if chid not in existing]
        
        for chid in new_entries:
            cursor.execute("INSERT INTO chips (chid) VALUES (%s)", (chid,))
        
        db_target.commit()
        print(f"{len(new_entries)} neue 'chid'-Werte wurden in roomregister.chips eingefügt.")
        cursor.close()
        db_target.close()
    except Error as err:
        print("Fehler bei der Synchronisation der Roomregister-Chips:", err)

def main():
    master_chids = get_master_chids()
    if master_chids:
        sync_roomregister_chips(master_chids)
    else:
        print("Keine Daten in der Master-Datenbank gefunden.")

if __name__ == "__main__":
    main()
