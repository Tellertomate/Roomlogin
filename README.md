# Roomlogin via RFID Chips
Made for the RFID-RC522 simular models maybe will work too.
A solution for a school to "Login" to a classroom as a student via RFID Chips.



# Installation

## 1. Install the requirements and repository
#### Updating and installing the requirements:
```
sudo apt update && sudo apt install python3 git nano tmux docker.io docker-compose -y
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
Open the file and fill in your passwords etc.
```
sudo nano docker-compose.yml
```
Then start the container:
```
sudo docker-compose up -d
```

---

#### Linux:
Documentary:
https://www.digitalocean.com/community/tutorials/how-to-install-mariadb-on-ubuntu-20-04
(Just use docker)

---

### Create and set up the databases
#### Master: (MYSQL)
Fill in the host ip, username, passwort etc. in the mastersetup.py file and then execute it.
```
cd server/db_setup
```
```
sudo nano mastersetup.py
```
```
sudo python mastersetup.py
```

---

#### Roomclient: (MYSQL)
Do the same installation procedure on a different server which is going to be the roomclient and build the roomclient database.
```
cd roomclient/db_setup
```
```
sudo nano roomsetup.py
```
```
sudo python roomsetup.py
```

## 3. Editing and automating the scripts
To sync the necessary data between the databases you will need the provided chipsync and mastersync scripts
- On your Master server go to /server
```
cd server
```
Edit chipsync.py and fill out the host's, password's etc. AND THE ROOMID!
```
sudo nano chipsync.py
```
Automatically execute them every 5 mins
```
sudo crontab -e
```
At the end, add the lines:
```
0 * * * * /usr/bin/python3 /path/to/chipsync.py
0 * * * * /usr/bin/python3 /path/to/mastersync.py
```
---

#### Starting the client reader
On the Roomclient server go to /roomregister
```
cd roomregister
```
Open the login.py file and fill out the host's, password's etc.
```
sudo nano login.py
```
Create a Tmux session
```
sudo tmux
```
And start the script
```
sudo python3 login.py
```

## 4. Filling in information
You only edit information in the master db! Now you should fill in the coredata on the masterdb (rooms, students and chips) where you connect students and chips in the assignments table and fill in the roomid's into the corresponding login scripts.
- To create, change or delete entries in the students, chips, rooms and assignments tables use the entrieinteractiontool.py
```
sudo python3 entrieinteractiontool.py
```



