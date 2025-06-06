CREATE DATABASE IF NOT EXISTS master CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE master;

CREATE TABLE IF NOT EXISTS chips (
    chid VARCHAR(50) NOT NULL PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS rooms (
    roomid INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    name VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    stid INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    firstname VARCHAR(50) NOT NULL,
    secondname VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS assignments (
    oid INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    stid INT NOT NULL,
    chid VARCHAR(50) NOT NULL,
    FOREIGN KEY (stid) REFERENCES students(stid) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (chid) REFERENCES chips(chid) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS master (
    lfnr INT AUTO_INCREMENT PRIMARY KEY,
    oid INT NOT NULL,
    roomid INT NOT NULL,
    time DATETIME NOT NULL,
    FOREIGN KEY (oid) REFERENCES assignments(oid),
    FOREIGN KEY (roomid) REFERENCES rooms(roomid)
);

