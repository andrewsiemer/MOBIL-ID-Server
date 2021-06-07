# MOBIL-ID Server

![CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)

## What is MOBIL-ID?

#### A Python web service & embedded reader for Apple Wallet & Google Pay

The MOBIL-ID project is an engineering systems capstone project for Oklahoma Christian University. The team’s mission statement is to create a mobile platform front-end to Oklahoma Christian University’s user management system. Students and Faculty will use their mobile ID to gain chapel attendance, enter the university cafeteria, and pay using Eagle Bucks.

### MOBIL-ID Server
The MOBIL-ID Server is a Python web service responsible for creating, deploying, and updating passes using Apple PassKit & Google Pay API. It tracks the pass’s complete lifecycle. When a user requests a pass, the server gets the user's data from OC’s database, creates a new pass, and signs it before delivering it to the user. It keeps a log of every pass it creates. When a user adds the pass to Apple Wallet, the pass will send a registration request to our server. The server will log the device id and pass relationship. When users data is changed, the MOBIL-ID server then knows what device to send the update push notification to. If a user deletes a pass of their device, the server will receive a request to delete the pass and it will be deleted from the server’s database and no longer receive updates. The user will also recieve real-time push notifications when pass data has change.

![OC Graphic](/static/team/OC-graphic.jpeg)

### MOBIL-ID Reader
The MOBIL-ID Reader is a slave device responsible for scanning MOBIL-ID passes. It captures the QR data from a scanned pass and sends it in a GET request to the MOBIL-ID Server. The MOBIL-ID Server returns the associated user ID number. The MOBIL-ID Reader then hands the ID number to the transactional system via the USB connection. [View MOBIL-ID Reader](https://github.com/andrewsiemer/MOBIL-ID-Reader)

### The MOBIL-ID Team
- Andrew Siemer - Electrical/Software Engineer - Team Lead
- Jacob Button - Electrical/Software Engineer
- Kyla Tarpey - Electrical Engineer
- Zach Jones - Computer/Software Engineer

### Acknowledgments
- Steve Maher - Mentor
- Luke Hartman - Customer
- Peyton Chenault - System Integrator

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/).

---

## Installation (macOS/Linux)
### Install Prerequisites
* Python 3
* Python3-pip
* Python3-venv
* Git

> You should also always use `sudo apt update && apt upgrade` before starting the installation process to make sure your system packages are up to date.

Install Python 3 using:
```sh
sudo apt-get install python3
```

Install PIP using:
```sh
sudo apt-get install python3-pip
```

Install Venv using:
```sh
sudo apt-get install python3-venv
```

Install Git using:
```sh
sudo apt install git-all -y
```

### Download MOBIL-ID Server Software
In the current users home directory, run one of the commands below:
#### From GitHub:
```sh
git clone https://github.com/andrewsiemer/MOBIL-ID-Server
```
#### From BitBucket:
To use BitBucket, you must be authorized to access the repository. Change  `<user>` with your BitBucket username and enter your password when prompted.
```sh
git clone https://<user>@bitbucket.org/OklahomaChristian/mobil-id-server/src/main/
```
### Create Virtual Environment
Then create a virtual environment in the `MOBIL-ID-Server/` directory with:
```sh
python3 -m venv MOBIL-ID-Server/
```

### Activate Virtual Environment
```sh
cd MOBIL-ID-Server/
source bin/activate
```

### Install Dependencies
Now that we are inside the environment we need to install our dependencies using:
```sh
sudo apt-get install build-essential libssl-dev libffi-dev python-dev
```

### Update PIP
```sh
python3 -m pip install --upgrade pip
```

### Install PIP Requirements
Install all requirements at once using:
```sh
pip3 install -r requirements.txt
```

### Getting the Certificates
1) Get Apple WWDR Certificate

* Download the certificate at: http://developer.apple.com/certificationauthority/AppleWWDRCA.cer
* Open Terminal and navigate to the folder where you downloaded the file
* Convert the DER file it into a PEM:
```shell
openssl x509 -inform der -in AppleWWDRCA.cer -out wwdr.pem
```
* Move file to `certificates/`

2) Get a Pass Type Id

* Login to your Apple Developer Account 
* Navigate to Certificates, Identifiers & Profiles -> Identifiers -> (+) -> Pass Type IDs
	* Enter a Description & Identifier then click 'Register'
* Next, under 'Identifiers' click on the one you just created (pass.xxx.xxx)
	* Under 'Production Certificates' -> 'Create Certificate'
	* Upload a Certificate Signing Request (Follow the 'Learn more' link for help)
	* Finally, click Continue -> Download

3) Get a Pass Type Certificate

* Double-click the pass file you downloaded to install it to your keychain
* Export the pass certificate as a p12 file:
    * Open Keychain Access -> Locate the pass certificate (under the login keychain) -> Right-click the pass -> Export
    * Make sure the File Format is set to `Personal Information Exchange (.p12)` and export to a convenient location
	* Write down the password used to encrypt the file
	> You must set a password for the PEM file or you'll get errors when attempt to generate Apple pass files
* Generate the necessary certificate/key PEM file
    * Open Terminal and navigate to the folder where you exported the p12 file
    * Generate the pass PEM file:
	```sh
	openssl pkcs12 -in "Certificates.p12" -clcerts -out pass.pem
	```
	* Enter the password you just created when exporting to p12
* Move file to `certificates/`
> If any certificate is expired, you won't be able to create a pass

### Configuring the Server
First, we need to change the file named `config_sample.py` to `config.py`.
Now open `config.py` and set these variables:

* DEBUG - *bool.* toggles logging, `/docs` test endpoint, and `pash_hash` viability
* WEB_SERVICE_URL - *str.* your domain (must include `https://`)
* OC_SHARED_SECRET - *str.* shared secret with client
* PASS_TYPE_IDENTIFIER - *str.* the Pass Type ID from step 2 above
* TEAM_IDENTIFIER - *str.* your Team ID found on developer.apple.com
* PASS_TYPE_CERTIFICATE_PATH - *str.* path to Pass Type cert (should be `'certificates/pass.pem'`)
* PEM_PASSWORD - *str.* password used when exporting the cert key
* WWDR_CERTIFICATE_PATH - *str.* path to WWDR cert (should be `'certificates/wwdr.pem'`)
* ISSUER_ID - *str.* identifier of Google Pay API for Passes Merchant Center
* SAVE_LINK - *str.* (default: `'https://pay.google.com/gp/v/save/'`)
* VERTICAL_TYPE - *str.* (default: `'VerticalType.LOYALTY'`)
* CLASS_ID - *str.* the created Class ID from Google Developer portal
* SERVICE_ACCOUNT_EMAIL_ADDRESS - *str.* Google Developer service account email address
* SERVICE_ACCOUNT_FILE - *str.* path to Google credential cert (should be `'certificates/...json'`)
* ORIGINS - *list* (default: `[WEB_SERVICE_URL]`)
* AUDIENCE - *str.* (default: `'google'`)
* JWT_TYPE - *str.* (default: `'savetoandroidpay'`)
* SCOPES - *list* (default: `['https://www.googleapis.com/auth/wallet_object.issuer']`)
* EMAIL_PORT - *int* email port for ssl (default: `465`)
* SMTP_SERVER - *str.* smtp server address of server email account (default: `'smtp.gmail.com'`)
* SENDER_EMAIL - *str.* server email account login
* EMAIL_PASSWORD - *str.* password to server email account
* RECEIVER_EMAIL - *list* contains receiver email addresses as strings
* WHITELIST - *list* contains whitelisted ID numbers as strings

### Start Development Server
To start server on your local network include the host tag with your ip address.
```sh
uvicorn main:app --reload --host <ip>
```

### View Registation Page
```
http://<ip>:8000
```

### Done!
You can now safely shutdown the development server by pressing `^C`.
Then, leave the virtual environment with:
```sh
deactivate
```

## Deploying to a Production Environment (Linux)

## Prerequisites
* Domain name is setup with A record of server address
* You have an existing SSL certificate for your domain

> It is recommended to dedicate a new user in the sudo group for running the server (never use root). You should also consider changing your computer's hostname for easier access.

### Uncomplicated Firewall:
Install UFW using:
```sh
sudo apt install ufw
```

Next, we need to configure UFW using:
```sh
sudo ufw default allow outgoing
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow http/tcp
sudo ufw allow https/tcp
```

Then, we will enable our configuration with:
```sh
sudo ufw enable
```

Lastly, we will check that we configured UFW correctly using the command below. Check to make sure ssh(22), http(80), & https(443) are allowed.
```sh 
sudo ufw status
```

> If configured incorrectly, you could block yourself from ssh access to the computer.

### Nginx
Install Nginx using:
```sh
sudo apt install nginx
```

To configure Nginx proxy for our server, we need to first delete the default configuration.
```sh
sudo rm /etc/nginx/sites-enabled/default
```

Next, we will create our own configuration file using:
```sh
sudo nano /etc/nginx/sites-enabled/server
```

Inside the file paste the following lines:
```sh
server {
	server_name <www> <non-www>;

	location /static {
		alias /path/to/MOBIL-ID-Server/static;
	}

	location / {
		proxy_pass http://localhost:8000;
		include /etc/nginx/proxy_params;
		proxy_redirect off;
	}

	listen 443 ssl; 
	listen [::]:443 ssl;
	ssl_certificate /path/to/SSL-cert.pem;
	ssl_certificate_key /path/to/SSL-key.pem;
}
server {
	if ($host = <www>) {
		return 301 https://$host$request_uri;
	}

	if ($host = <non-www>) {
		return 301 https://$host$request_uri;
	}
	listen 80;
	listen [::]:443;
	server_name <www> <non-www>;
	return 404;
}
```

Then, change `<www>` to the www domain of the server & `<non-www>` to the non-www domain of the server. Change the `/path/to/` to the actual path to the downloaded software, certificate, & key.

Save and exit the file using `^X` then type `y` and click your `enter/return` key.

Check the configuration file contents using:
```sh
sudo nginx -t
```

Lastly, we want to restart Nginx to use our new configuration using:
```sh
sudo system to restart nginx
```

### Supervisor
Install Supervisor using:
```sh
sudo apt install supervisor
```

Create a new configuration file using:
```sh
sudo nano /etc/supervisor/conf.d/server.conf
```

Inside the file paste the following lines:
```sh
[program:server]
directory=/path/to/MOBIL-ID-Server
command=/path/to/MOBIL-ID-Server/bin/gunicorn -w <num-workers> -k uvicorn.workers.UvicornWorker main:app
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/server/server.err.log
stdout_logfile=/var/log/server/server.out.log
```

Then, change `<num-workers>` to the number of available processors the computer has plus one. Change the `/path/to/` to the actual path to the downloaded software.


Save and exit the file using `^X` then type `y` and click your `enter/return` key.

Create the server log files with:
```sh
sudo mkdir -p /var/log/server
sudo touch /var/log/server/server.err.log
sudo touch /var/log/server/server.out.log
```

Lastly, we want to restart Supervisor to use our new configuration using:
```sh
sudo supervisorctl reload
```

### Test the Server
Your server should now be available in a browser using:
`https://<your-domain>`

### Turn Off Debug Mode
Since you are know running the server in a production environment, you should turn off debug mode.
To do this we first need to open the server config file.
```sh
sudo nano /path/to/MOBIL-ID-Server/config.py
```
Once inside the file change the `DEBUG` flag to `False`

Save and exit the file using `^X` then type `y` and click your `enter/return` key.

Since we changed files in the active server, we need to reload it using:
```sh
sudo supervisorctl reload
```

### Update Server
You can update the server at anytime from the remote repository using:
```sh
cd /path/to/MOBIL-ID-Server
git pull
sudo supervisorctl reload
```

---

## References
### FastAPI
* [First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/) - basic web service functionality
* [Templates](https://fastapi.tiangolo.com/advanced/templates/) - serve custom webpages to user
* [Custom Response](https://fastapi.tiangolo.com/advanced/custom-response/) - send pass file to user
* [SQL Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/) - store device, pass, & registration data in a database
* [Form Data](https://fastapi.tiangolo.com/tutorial/request-forms/) - handle submitted form data
* [Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) - perform async background tasks

### Apple
* [Wallet Developer Guide](https://developer.apple.com/library/archive/documentation/UserExperience/Conceptual/PassKit_PG/index.html#//apple_ref/doc/uid/TP40012195-CH1-SW1) - guide & background info for Apple Wallet passes
* [Apple PassKit Bundle Documentation](https://developer.apple.com/library/archive/documentation/UserExperience/Reference/PassKit_Bundle/Chapters/TopLevel.html) - pass file framework
* [Apple PassKit Web Service Documentation](https://developer.apple.com/library/archive/documentation/PassKit/Reference/PassKit_WebService/WebService.html#//apple_ref/doc/uid/TP40011988) - communicate with deployed passes
* [Pass Bundle Validator](https://pkpassvalidator.azurewebsites.net) - validates a created pass file with framework
* [Sending Push Notifications using Terminal](https://developer.apple.com/documentation/usernotifications/sending_push_notifications_using_command-line_tools) - tell device to check for pass update
