# Roomlogin via RFID Chips
Made for the RFID-RC522 simular models maybe will work too.
A solution for a school to "Login" to a classroom as a student via RFID Chips.



# Installation

## 1. Install the requirements and repository
#### Updating and installing the requirements:
```
sudo apt update && sudo apt install python3 git nano tmux docker.io docker-compose
```
#### Cloning the repository and changing into it:
```
sudo git clone https://github.com/Tellertomate/Roomlogin.git && cd Roomlogin
```

## 2. Create Databases
Lets get your Databases up and running to store all the information.
We will be using mariadb.

### Install Mariadb
#### Docker Compose:
##### Open the file and fill in your passwords etc.
```
sudo nano docker-compose.yml
```
##### Then start the container:
```
sudo docker-compose up -d
```
#### Linux:
Documentary:
https://www.digitalocean.com/community/tutorials/how-to-install-mariadb-on-ubuntu-20-04
(Just use docker)

### Create and set up the databases
#### Master: (MYSQL)
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
CREATE TABLE assignments (oid INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
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

#### Roomclient: (MYSQL)
Do the same installation procedure on a different server which is going to be the roomclient and build the roomclient database.
```
CREATE DATABASE roomregister
USE roomregister;
```
```
CREATE TABLE chips (chid VARCHAR(50) NOT NULL PRIMARY KEY);
```
```
CREATE TABLE login (lfnr INT AUTO_INCREMENT NOT NULL PRIMARY KEY, chid VARCHAR(50) NOT NULL, roomid INT NOT NULL, time DATETIME DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (chid) REFERENCES chips(chid));
```

## 3. Editing and automating the scripts
To sync the necessary data between the databases you will need the provided chipsync and mastersync scripts
- On your Master server go to /server
```
cd server
```
- Edit chipsync.py and fill out the host's, password's etc. AND THE ROOMID!
```
sudo nano chipsync.py
```
- Automatically execute them every 5 mins
```
sudo crontab -e
```
- At the end, add the lines:
```
0 * * * * /usr/bin/python3 /path/to/chipsync.py
0 * * * * /usr/bin/python3 /path/to/mastersync.py
```
#### Starting the client reader
- On the Roomclient server go to /roomregister
```
cd roomregister
```
- Open the login.py file and fill out the host's, password's etc.
```
sudo nano login.py
```
- Create a Tmux session
```
sudo tmux
```
- And start the script
```
sudo python3 login.py
```

## 4. Filling in information
You only edit information in the master db! Now you should fill in the coredata on the masterdb (rooms, students and chips) where you connect students and chips in the assignments table and fill in the roomid's into the corresponding login scripts.
- To create, change or delete entries in the students, chips, rooms and assignments tables use the entrieinteractiontool.py
```
sudo python3 entrieinteractiontool.py
```



