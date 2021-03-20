'''
schemas.py: Classes for verifying users & creating user passes
'''

import subprocess, json, secrets, requests, time
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta
import pytz

from sqlalchemy.orm import Session

import include.crud as crud, include.utils as utils, config
from include.passkit import Pass, Barcode, Generic, BarcodeFormat, Alignment, Location, IBeacon

class User():
    '''
    Check for valid users
    '''
    def __init__(self, entered_id: str, entered_pin: str = None):
        self.valid = True

        self.id = entered_id
        token = utils.encrypt(self.id + '-' + str(time.time()), config.OC_SHARED_SECRET)
        request_URL = 'https://account.oc.edu/mobilepass/details/' + self.id + '?token=' + token
        
        if config.DEBUG:
            print(request_URL)
        
        r = requests.get(request_URL, timeout=3)
        try:
            # try to parse request body
            self.data = r.json()
        except:
            # if bad response from OC,
            # invalidate user
            self.valid = False
        else:
            # the json data was parsed without error
            if entered_pin:
                # if a login pin was entered,
                # check for validation
                self.validate(entered_pin)
            if self.is_valid():
                # if user is valid,
                # create user object
                self.create()
    
    def validate(self, entered_pin):
        self.pin = self.data['IDPin']
        if entered_pin != self.pin:
            # if the given pin is not the correct pin,
            # invalidate user
            self.valid = False
        
        return self.valid
        

    '''
    User is valid, store data in python object
    '''
    def create(self):
        # parse User data into reusable variables
        self.name = self.data['FullName']
        self.photo_URL = self.data['PhotoURL']
        self.eagle_bucks = self.data['EagleBucks']
        self.meals_remaining = self.data['MealsRemaining']
        self.kudos_earned = str(self.data['KudosEarned'])
        self.kudos_required = str(self.data['KudosRequired'])
        self.id_pin = self.data['IDPin']
        self.print_balance = self.data['PrintBalance']
        try:
            self.mailbox = self.data['Mailbox']
        except:
            self.mailbox = None
    
    def is_valid(self):
        # returns if the given user data is valid User
        return self.valid

class Pkpass():
    '''
    Create pkpass file for given User
    '''
    def __init__(self, db: Session, serial_number: str):
        # parse User data into reusable variables
        user_pass = crud.get_pass(db, serial_number)

        passinfo = Generic()
        passinfo.addPrimaryField('name', user_pass.name)
        passinfo.addSecondaryField('cash', '$' + str(user_pass.eagle_bucks), 'Eagle Bucks', 'You have %@ Eagle Bucks remaining.', textAlignment=Alignment.LEFT)
        passinfo.addSecondaryField('meals', user_pass.meals_remaining, 'Meals Remaining', 'You have %@ meal swipes remaining.', textAlignment=Alignment.CENTER)
        passinfo.addSecondaryField('ethos', user_pass.kudos_earned + "/" + user_pass.kudos_required, 'Kudos', 'You have %@ Kudos of your Semester Goal.', textAlignment=Alignment.RIGHT)
        passinfo.addBackField('pin', user_pass.id_pin, 'ID Pin')
        passinfo.addBackField('print', user_pass.print_balance, 'Print Balance', 'Your print balance is now %@.')
        if user_pass.mailbox:
            passinfo.addBackField('boxnumber', user_pass.mailbox, 'Mailbox Nuber')
        passinfo.addBackField('tribute', 'Andrew Siemer, Jacob Button, Kyla Tarpey, & Zach Jones', 'Created by Team MOBIL-ID')
        if config.DEBUG:
            passinfo.addBackField('hash', user_pass.pass_hash, 'Pass Hash')

        passfile = Pass(passinfo, \
            passTypeIdentifier=user_pass.pass_type , \
            organizationName='Oklahoma Chrisitian University' , \
            teamIdentifier=config.TEAM_IDENTIFIER)

        passfile.sharingProhibited = True
        passfile.webServiceURL = config.WEB_SERVICE_URL
        passfile.authenticationToken = user_pass.auth_token
        passfile.description = 'OC ID'
        passfile.associatedStoreIdentifiers = [ 306012905, ]
        passfile.foregroundColor = 'rgb(255, 255, 255)'
        passfile.backgroundColor = 'rgb(128, 20, 41)'
        passfile.labelColor = 'rgb(255, 255, 255)'
        passfile.serialNumber = user_pass.serial_number
        passfile.barcode = Barcode(user_pass.pass_hash, BarcodeFormat.QR, user_pass.serial_number)   
        passfile.locations = list()
        passfile.locations.append(Location(35.611219, -97.467255, relevantText='Welcome to Garvey! Tap to scan your ID.', maxDistance=20))
        passfile.locations.append(Location(35.6115, -97.4695, relevantText='Welcome to the Branch! Tap to scan your ID.', maxDistance=20))
        passfile.locations.append(Location(35.61201, -97.46850, relevantText='Welcome to the Brew! Tap to scan your ID.', maxDistance=20))
        passfile.ibeacons = list()
        passfile.ibeacons.append(IBeacon('1F234454-CF6D-4A0F-ADF2-F4911BA9FFA9', 1, 1, 'Tap to scan your ID.'))
        # Make pass expire after 25 hours, 
        # If pass goes unused during day batch update will update
        # passfile.expirationDate = str((pytz.utc.localize(datetime.utcnow())+timedelta(hours=25)).isoformat())

        # Including the icon and logo is necessary for the passbook to be valid.
        passfile.addFile('icon.png', open('base.pass/icon.png', 'rb'))
        passfile.addFile('icon@2x.png', open('base.pass/icon@2x.png', 'rb'))
        passfile.addFile('icon@3x.png', open('base.pass/icon@3x.png', 'rb'))
        passfile.addFile('logo.png', open('base.pass/logo.png', 'rb'))
        passfile.addFile('logo@2x.png', open('base.pass/logo@2x.png', 'rb'))
        passfile.addFile('logo@3x.png', open('base.pass/logo@3x.png', 'rb'))

        try:
            # Add user photo with different device resolution support
            response = requests.get(user_pass.photo_URL)
            img = Image.open(BytesIO(response.content))

            # Add 3x resolution thumbnail
            img = img.resize((204,270))
            img_byte = BytesIO()
            img.save(img_byte, format='PNG')
            passfile.addFile('thumbnail@3x.png', img_bytes=img_byte.getvalue())
            
            # Add 2x resolution thumbnail
            img = img.resize((136,180))
            img_byte = BytesIO()
            img.save(img_byte, format='PNG')
            passfile.addFile('thumbnail@2x.png', img_bytes=img_byte.getvalue())
            
            # Add 1x resolution thumbnail
            img = img.resize((68,90))
            img_byte = BytesIO()
            img.save(img_byte, format='PNG')
            passfile.addFile('thumbnail.png', img_bytes=img_byte.getvalue())
        except:
            # Include default identification photo
            passfile.addFile('thumbnail.png', open('base.pass/thumbnail.png', 'rb'))
            passfile.addFile('thumbnail@2x.png', open('base.pass/thumbnail@2x.png', 'rb'))
            passfile.addFile('thumbnail@3x.png', open('base.pass/thumbnail@3x.png', 'rb'))

        # Create and output the Passbook file (.pkpass)
        passfile.create(config.PASS_TYPE_CERTIFICATE_PATH, config.PASS_TYPE_CERTIFICATE_PATH, config.WWDR_CERTIFICATE_PATH, 'siemer', 'passes/' + user_pass.serial_number + '.pkpass')
