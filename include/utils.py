'''
utils.py: Reusable functions to interact with the main program.
'''
import secrets, sys, base64, smtplib, ssl
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from apns2.client import APNsClient
from apns2.payload import Payload
from hashlib import md5
from Cryptodome import Random
from Cryptodome.Cipher import AES

import config, include.crud as crud, include.schemas as schemas

class AES256():
    '''
    Encrypts & decrypts a string using a passphrase and AES-256
    '''
    def __init__(self):
        self.py2 = sys.version_info[0] == 2

        self.BLOCK_SIZE = 16
        self.KEY_LEN = 32
        self.IV_LEN = 16

    def encrypt(self, raw, passphrase):
        salt = Random.new().read(8)
        key, iv = self.__derive_key_and_iv(passphrase, salt)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return base64.b64encode(b'Salted__' + salt + cipher.encrypt(self.__pkcs7_padding(raw)))

    def decrypt(self, enc, passphrase):
        ct = base64.b64decode(enc)
        salted = ct[:8]
        if salted != b'Salted__':
            return ""
        salt = ct[8:16]
        key, iv = self.__derive_key_and_iv(passphrase, salt)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return self.__pkcs7_trimming(cipher.decrypt(ct[16:]))

    def __pkcs7_padding(self, s):
        s_len = len(s if self.py2 else s.encode('utf-8'))
        s = s + (self.BLOCK_SIZE - s_len % self.BLOCK_SIZE) * chr(self.BLOCK_SIZE - s_len % self.BLOCK_SIZE)
        return s if self.py2 else bytes(s, 'utf-8')

    def __pkcs7_trimming(self, s):
        if sys.version_info[0] == 2:
            return s[0:-ord(s[-1])]
        return s[0:-s[-1]]

    def __derive_key_and_iv(self, password, salt):
        d = d_i = b''
        enc_pass = password if self.py2 else password.encode('utf-8')
        while len(d) < self.KEY_LEN + self.IV_LEN:
            d_i = md5(d_i + enc_pass + salt).digest()
            d += d_i
        return d[:self.KEY_LEN], d[self.KEY_LEN:self.KEY_LEN + self.IV_LEN]

class Email():
    def __init__(self, subject: str, body: str):
        self.tag = '[MOBIL-ID]'
        self.subject = subject
        self.body = body
        self.signature = 'This is an automated message from the MOBIL-ID Server (' + config.WEB_SERVICE_URL + ').'

    def get_message(self):
        return 'Subject: ' + self.tag + ' ' + self.subject + '\n\n' + self.body + '\n\n\n' + self.signature
    
    def send(self):
        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(config.SMTP_SERVER, config.EMAIL_PORT, context=context) as server:
            server.login(config.SENDER_EMAIL, config.EMAIL_PASSWORD)
            server.sendmail(config.SENDER_EMAIL, config.RECEIVER_EMAIL, self.get_message())

def send_notification(subject: str, body: str):
    email = Email(subject, body)
    email.send()

def get_log(file: str):
    # open log file at current location
    file = open(file, 'r+')

    data = file.read()

    # clear current log file
    file.truncate(0)
    file.close()
    
    return data

def input_validate(id: str, pin: str):
    '''
    Quickly validate login input to not waste API call
    '''
    valid = True
    if len(id) == 7 and len(pin) == 4:
        try:
            int(id)
            int(pin)
        except:
            valid = False
    else:
        valid = False
    
    return valid

def unique_pass_hash(db: Session, num_bytes: int):
    '''
    Makes sure hash is unique in the database
    '''
    unique = False
    while(not unique):
        hash = secrets.token_urlsafe(num_bytes)

        db_pass = crud.get_pass_by_hash(db, hash)
        if not db_pass: # no pass has hash therefor unique
            unique = True

    return hash

def get_pass_file(db: Session, serial_number: str):
    '''
    Gets the pass file associated with the given serial_number
    '''
    return FileResponse('passes/' + serial_number + '.pkpass', media_type='application/vnd.apple.pkpass', filename='ocid.pkpass')

def force_pass_update(db: Session, serial_number: str):
    crud.update_hash(db, serial_number)
    push_pass_update(db, serial_number)

def update_pass(db: Session, serial_number: str):
    '''
    Updates pass with serial_number
    '''
    user = schemas.User(serial_number)
    if user.is_valid():
        # if user is valid,
        # update database pass
        crud.update_db_pass(db, user)
        # start background task to update pass with new pass_hash
        push_pass_update(db, serial_number)

def push_pass_update(db: Session, serial_number: str):
    push_tokens = crud.get_device_list_by_pass(db, serial_number)
    for push_token in push_tokens:
            send_apn(push_token)

def send_apn(push_token: str):
    '''
    Sends an empty APN to the given device push_token
    '''
    payload = Payload()
    client = APNsClient(config.PASS_TYPE_CERTIFICATE_PATH, use_sandbox=False, use_alternative_port=False)
    client.send_notification(push_token, payload, config.PASS_TYPE_IDENTIFIER)
