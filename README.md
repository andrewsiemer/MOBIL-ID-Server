## Installation (macOS)
### Prerequisites
- Python 3.x
- Virtualenv 20.x.x

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
* PASS_TYPE_IDENTIFIER - the Pass Type ID from step 2 above
* TEAM_IDENTIFIER - your Team ID found on developer.apple.com
* WEB_SERVICE_URL - your domain (if running locally it will be something like 192.168.0.X:8000)
* PASS_TYPE_CERTIFICATE_PATH - path to Pass Type cert (should be `'certificates/pass.pem'`)
* WWDR_CERTIFICATE_PATH - path to WWDR cert (should be `'certificates/wwdr.pem'`)
* OC_SHARED_SECRET - shared secret with client

> All variables should be strings

### Create Virtual Environment
Open Terminal and go to `MOBIL-ID-Software/` directory:
```sh
cd /path/to/mobil-id-software
```
Create Virtual Environment in `server` folder:
```sh
python3 -m venv server
```

### Activate Virtual Environment
```sh
cd server
source bin/activate
```
### Install Dependencies
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
### Start Server
To start server on your local network include the host tag with your ip address.
```sh
uvicorn main:app --reload --host <ip>
```

### View Registation Page
```
http://<ip>:8000
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

### OC Related
* [OC Database example API call](https://account.oc.edu/mobilepass/details/1458777) - request for user data from OC database
* [AES-256 Encrytion](https://www.quickprogrammingtips.com/python/aes-256-encryption-and-decryption-in-python.html) - for ecrypting data requests to OC
