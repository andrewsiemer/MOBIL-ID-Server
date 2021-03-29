## What is MOBIL-ID?
#### A Python web service & embedded reader for Apple PassKit

The MOBIL-ID project is an engineering systems capstone project for Oklahoma Christian University. The team’s mission statement is to create a mobile platform front-end to Oklahoma Christian University’s user management system. Students and Faculty will use their mobile ID to gain chapel attendance, enter the university cafeteria, and pay using Eagle Bucks. While most of the MOBIL-ID Server is a closed-source system for security, the MOBIL-ID Reader is an open-source project.

### MOBIL-ID Server
The MOBIL-ID Server is a Python web service responsible for creating, deploying, and updating passes using Apple PassKit. It tracks the pass’s complete lifecycle. When a user requests a pass, the server gets the user's data from OC’s database, creates a new pass, and signs it before delivering it to the user. It keeps a log of every pass it creates. When a user adds the pass to Apple Wallet, the pass will send a registration request to our server. The server will log the device id and pass relationship. When users data is changed, the MOBIL-ID server then knows what device to send the update push notification to. If a user deletes a pass of their device, the server will receive a request to delete the pass and it will be deleted from the server’s database and no longer receive updates.

### The MOBIL-ID Team
- Andrew Siemer - Electrical/Software Engineer - Team Lead
- Jacob Button - Electrical/Software Engineer
- Kyla Tarpey - Electrical Engineer
- Zach Jones - Computer/Software Engineer

### Acknowledgments
- Steve Maher - Professor/Mentor
- Luke Hartman - Customer/Mentor





## Installation (macOS/Linux)
### Install Prerequisites
* Python 3
* Python3-pip
* Python3-venv
* Git

> You should also always use `sudo apt update && apt upgrade` before starting the installation process to make sure your system packages are up to date.

Install Python 3.8 using:
```sh
sudo apt-get install python3.8
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

### Download MOBIL-ID Server software
In the current users home directory, run:
```sh
git clone https://github.com/andrewsiemer/MOBIL-ID-Server
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
sudo apt-get install libssl-dev swig python3-dev gcc build-essential libssl-dev libffi-dev python-dev
```

### Update PIP
```sh
pip install --upgrade --force-reinstall pip virtualenv
```

### Install PIP Requirements
Install all requirements at once using:
```sh
pip3 install -r requirements.txt
```

### Getting the Certificates

> This step can be skipped if the certificates have already been provided.

1) Get Apple WWDR Certificate
* Certificate is available at: http://developer.apple.com/certificationauthority/AppleWWDRCA.cer
* Convert it into a ".pem" file:
```shell
	$ openssl x509 -inform der -in AppleWWDRCA.cer -out wwdr.pem
```
* Move file to `certificates/`

2) Get a Pass Type Id
* Visit the iOS Provisioning Portal -> Pass Type IDs -> New Pass Type ID
* Select pass type id -> Configure (Follow steps and download generated pass.cer file)
* Import downloaded certificate into Keychain Access on your Mac.
* Export the certificate from Keychain Access into a `.pem` file
* Move file to `certificates/` and name it `pass.pem`

> Note that if any certificate is expired, you won't be able to create a pass.

### Configuring the Server
First, we need to change the file named `config_sample.py` to `config.py`.
Now open `config.py` and set these variables:
* DEBUG - *bool.* toggles logging, `/docs` test endpoint, and `pash_hash` viability
* PASS_TYPE_IDENTIFIER - *str.* the Pass Type ID from step 2 above
* TEAM_IDENTIFIER - *str.* your Team ID found on developer.apple.com
* WEB_SERVICE_URL - *str.* your domain (if running locally it will be something like 192.168.0.X:8000)
* PASS_TYPE_CERTIFICATE_PATH - *str.* path to Pass Type cert (should be `'certificates/pass.pem'`)
* WWDR_CERTIFICATE_PATH - *str.* path to WWDR cert (should be `'certificates/wwdr.pem'`)
* OC_SHARED_SECRET - *str.* shared secret with client

### Start Development Server
To start server on your local network include the host tag with your ip address.
```sh
uvicorn main:app --reload --host <ip>
```

### View Registation Page
```
http://<ip>:8000
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
[program: server]
directory=/path/to/MOBIL-ID-Server
command=/path/to/MOBIL-ID-Server/bin/gunicorn -w <num-workers> run:app
user=admin
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/server/server.err.log
stdout_logfile=/var/log/server/server.out.log
```

Then, change `<num-workers>` to the number of available processors the computer has plus one. Change the `/path/to/` to the actual path to the downloaded software.

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

### Update Server
You can update the server from the main repository using:
```sh
cd /path/to/MOBIL-ID-Server
git pull
sudo supervisorctl reload
```

## Reference Links
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
