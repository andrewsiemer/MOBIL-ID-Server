'''
crud.py: Reusable functions to interact with the data in the database.
CRUD comes from: Create, Read, Update, and Delete.
'''

import secrets
from datetime import datetime

from sqlalchemy.orm import Session, load_only

import include.utils as utils, config
from include.schemas import User, Pkpass
from include.models import Device, Pass, Registration

def get_device(db: Session, device_id: str):
    return db.query(Device).filter(Device.device_id==device_id).first()

def get_pass(db: Session, serial_number: str, auth_token: str = None):
    db_pass = db.query(Pass).filter(Pass.serial_number==serial_number).first()
    if auth_token:
        db_pass = db.query(Pass).filter(Pass.serial_number==serial_number,Pass.auth_token==auth_token).first()
    return db_pass

def get_pass_by_hash(db: Session, pass_hash: str):
    return db.query(Pass).filter(Pass.pass_hash==pass_hash).first()

def get_all_passes(db: Session):
    serial_numbers = list()
    
    db_passes = db.query(Pass.serial_number).all()
    for db_pass in db_passes:
        serial_numbers.append(db_pass[0])

    return serial_numbers

def get_pass_list_by_device(db: Session, device_id: str, passesUpdatedSince: str = None):
    serial_numbers = list()

    registrations = get_registrations_by_device(db, device_id)

    # covert given string to datetime obj for comparisons
    if passesUpdatedSince:
        updated_since = datetime.strptime(str(passesUpdatedSince), '%Y-%m-%d %H:%M:%S')

    last_updated = datetime.min
    for curr_pass in registrations:
        curr_pass_last_update = get_pass(db, curr_pass.serial_number).last_update
        if passesUpdatedSince:
            # If passesUpdatedSince tag was sent in get request
            # only get passes updated after the tag
            if updated_since < curr_pass_last_update:
                serial_numbers.append(curr_pass.serial_number)
        else:
            # Get all pass serial_numbers associated with device
            serial_numbers.append(curr_pass.serial_number)
        if last_updated < curr_pass_last_update:
                last_updated = curr_pass_last_update
    
    return last_updated, serial_numbers

def get_device_list_by_pass(db: Session, serial_number: str):
    push_tokens = list()

    devices = get_registrations_by_pass(db, serial_number)

    for curr_device in devices:
        device = get_device(db, curr_device.device_id)
        push_tokens.append(device.push_token)
    
    return push_tokens

def get_registration(db: Session, device_id: str, serial_number: str):
    return db.query(Registration).filter(Registration.device_id==device_id,Registration.serial_number==serial_number).first()

def get_registration_by_device(db: Session, device_id: str):
    return db.query(Registration).filter(Registration.device_id==device_id).first()

def get_registrations_by_device(db: Session, device_id: str):
    return db.query(Registration).filter(Registration.device_id==device_id).all()

def get_registrations_by_pass(db: Session, serial_number: str):
    return db.query(Registration).filter(Registration.serial_number==serial_number).all()

def add_device(db: Session, device_id: str, push_token: str):
    device = Device()
    device.device_id = device_id
    device.push_token = push_token

    db.add(device)
    db.commit() # commit new registation to database
    db.refresh(device)
    return device

def add_pass(db: Session, user: User):
    db_pass = Pass()
    db_pass.pass_type = config.PASS_TYPE_IDENTIFIER
    db_pass.serial_number = user.id
    db_pass.last_update = datetime.utcnow().replace(microsecond=0)
    db_pass.pass_hash = utils.unique_hash(db, 32)
    db_pass.auth_token = secrets.token_urlsafe(32)
    db_pass.name = user.name
    db_pass.photo_URL = user.photo_URL
    db_pass.eagle_bucks = user.eagle_bucks
    db_pass.meals_remaining = user.meals_remaining
    db_pass.kudos_earned = user.kudos_earned
    db_pass.kudos_required = user.kudos_required
    db_pass.id_pin = user.id_pin
    db_pass.print_balance = user.print_balance
    db_pass.mailbox = user.mailbox

    db.add(db_pass)
    db.commit()
    db.refresh(db_pass)
    return db_pass

def add_registration(db: Session, device_id: str, serial_number: str):
    registration = Registration()
    registration.device_id = device_id
    registration.serial_number = serial_number

    db.add(registration)
    db.commit() # commit new registation to database
    db.refresh(registration)
    return registration

def delete_device(db: Session, device_id: str):
    device = db.query(Device).filter(Device.device_id==device_id).first()
    db.delete(device)
    db.commit()

def delete_registration(db: Session, device_id: str, serial_number: str):
    registration = db.query(Registration).filter(Registration.device_id==device_id, Registration.serial_number==serial_number).first()
    db.delete(registration)
    db.commit()

def update_db_pass(db: Session, user: User):
    db_pass = db.query(Pass).filter(Pass.serial_number==user.id).first()
    db_pass.pass_type = config.PASS_TYPE_IDENTIFIER
    db_pass.serial_number = user.id
    db_pass.last_update = datetime.utcnow().replace(microsecond=0)
    db_pass.pass_hash = utils.unique_hash(db, 32)
    db_pass.name = user.name
    db_pass.photo_URL = user.photo_URL
    db_pass.eagle_bucks = user.eagle_bucks
    db_pass.meals_remaining = user.meals_remaining
    db_pass.kudos_earned = user.kudos_earned
    db_pass.kudos_required = user.kudos_required
    db_pass.id_pin = user.id_pin
    db_pass.print_balance = user.print_balance
    db_pass.mailbox = user.mailbox
    db.commit()
    Pkpass(db, user.id)

def update_hash(db: Session, serial_number: str):
    db_pass = db.query(Pass).filter(Pass.serial_number==serial_number).first()
    db_pass.pass_hash = utils.unique_hash(db, 32)
    db_pass.last_update = datetime.utcnow().replace(microsecond=0)
    db.commit()
    Pkpass(db, serial_number)

def force_pass_update(db: Session, serial_number: str):
    update_hash(db, serial_number)

    push_pass_update(db, serial_number)

def push_pass_update(db: Session, serial_number: str):
    push_tokens = get_device_list_by_pass(db, serial_number)
    for push_token in push_tokens:
            utils.send_apn(push_token)
