'''
utils.py: Reusable functions to interact with the main program.
'''
import hashlib, secrets
from base64 import b64encode, b64decode
from Crypto.Util import Padding
from Crypto.Cipher import AES
from Crypto import Random

from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from apns2.client import APNsClient
from apns2.payload import Payload

import include.crud as crud, config

'''
Quickly validate login input to not waste API call
'''
def input_validate(id: str, pin: str):
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

'''
Makes sure hash is unique in the database
'''
def unique_hash(db: Session, num_bytes: int):
    unique = False
    while(not unique):
        hash = secrets.token_urlsafe(num_bytes)

        db_pass = crud.get_pass_by_hash(db, hash)
        if not db_pass: # no pass has hash therefor unique
            unique = True

    return hash

'''
Gets the pass file associated with the given serial_number
'''
def get_pass_file(db: Session, serial_number: str):
    return FileResponse('passes/' + serial_number + '.pkpass', media_type='.pkpass', filename='ocid.pkpass')

'''
Encrypts a string of text with a given password using AES-256 encryption
'''
def encrypt(raw, password):
    private_key = hashlib.sha256(password.encode("utf-8")).digest()
    raw = Padding.pad(raw.encode('utf-8'), AES.block_size)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(private_key, AES.MODE_CBC, iv)
    return b64encode(iv + cipher.encrypt(raw)).decode("utf-8")

'''
Decrypts a string of text with a given password using AES-256 encryption
'''
def decrypt(enc, password):
    private_key = hashlib.sha256(password.encode("utf-8")).digest()
    enc = b64decode(enc)
    iv = enc[:16]
    cipher = AES.new(private_key, AES.MODE_CBC, iv)
    return Padding.unpad(cipher.decrypt(enc[16:]), AES.block_size).decode('utf-8')

'''
Sends an empty APN to the given device push_token
'''
def send_apn(push_token: str):
    payload = Payload()
    client = APNsClient(config.PASS_TYPE_CERTIFICATE_PATH, use_sandbox=False, use_alternative_port=False)
    client.send_notification(push_token, payload, config.PASS_TYPE_IDENTIFIER)
