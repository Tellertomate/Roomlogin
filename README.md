# Roomlogin via RFID Chips
A solution to "Login" into any room and 

## 1. Create Databases
Lets get your Databases up and running to store all the information.
We will be using mariadb.

### Install Mariadb
Docker Compose:
```
sudo docker-compose up -d
```
Linux:
```
sudo apt install mariadb-server usw bla
```

### Create and set up the databases
Master: (MYSQL)
```
CREATE DATABASE master
USE master;
```
```
CREATE TABLE chips (chid VARCHAR(50) NOT NULL PRIMARY KEY);
```
```
CREATE TABLE rooms (roomid INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
  name VARCHAR(20) NOT NULL);
```
```
CREATE TABLE students (stid INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
  firstname VARCHAR(50) NOT NULL,
  secondname VARCHAR(50) NOT NULL);
```
```
CREATE TABLE zuordnung (oid INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
  stid INT NOT NULL,
  chid VARCHAR(50) NOT NULL,
  FOREIGN KEY (stid) REFERENCES students(stid) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (chid) REFERENCES chips(chid) ON UPDATE CASCADE ON DELETE CASCADE);  
```
```
CREATE TABLE master (lfnr INT AUTO_INCREMENT PRIMARY KEY,
  oid INT NOT NULL, roomid INT NOT NULL,
  time DATETIME NOT NULL,
  FOREIGN KEY (oid) REFERENCES zuordnung(oid),
  FOREIGN KEY (roomid) REFERENCES rooms(roomid));
```

Roomclient: (MYSQL)




