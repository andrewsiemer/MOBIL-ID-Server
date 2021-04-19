'''
schemas.py: Classes for verifying users & creating user passes
'''

import subprocess, json, secrets, requests, time
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
from datetime import datetime, timedelta
import pytz

from sqlalchemy.orm import Session
import include.crud as crud, include.utils as utils, config
# Apple
from include.apple.passkit import Pass, Barcode, Generic, BarcodeFormat, Alignment, Location, IBeacon
# Google
import include.google.services as services
import include.google.restMethods

class User():
    '''
    Check for valid users
    '''
    def __init__(self, entered_id: str, entered_pin: str = None):
        self.valid = True

        self.id = entered_id
        token = utils.AES256()
        request_URL = 'https://account.oc.edu/mobilepass/details/' + self.id + '?token=' + token.encrypt(self.id + '-' + str(time.time()), config.OC_SHARED_SECRET).hex()
        
        tries = 3 # number of tries to get new data
        for i in range(tries):
            try:
                # try GET request
                r = requests.get(request_URL, timeout=3)
                # try to parse request body
                self.data = r.json()
            except:
                # exception occured, if tries left then continue trying
                # else re-raise original exception
                if i < tries - 1: # i is zero indexed
                    continue
                else:
                    # if bad response from OC,
                    # invalidate user
                    self.valid = False
                    raise
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
            break
    
    def validate(self, entered_pin):
        self.pin = self.data['IDPin']
        if entered_pin != self.pin:
            # if the given pin is not the correct pin,
            # invalidate user
            self.valid = False
        
        return self.valid
        
    def create(self):
        '''
        User is valid, store data in python object
        '''
        # parse User data into reusable variables
        self.name = self.data['FullName']
        self.photo_URL = self.data['PhotoURL']
        self.eagle_bucks = self.data['EagleBucks']
        self.meals_remaining = self.data['MealsRemaining']
        self.kudos_earned = str(self.data['KudosEarned'])
        self.kudos_required = str(self.data['KudosRequired'])
        self.id_pin = self.data['IDPin']
        try:
            self.print_balance = self.data['PrintBalance']
        except:
            self.print_balance = None
        try:
            self.mailbox = self.data['Mailbox']
        except:
            self.mailbox = None
    
    def is_valid(self):
        # returns if the given user data is valid User
        return self.valid

class Pkpass():
    '''
    Apple Pass Object
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
        if user_pass.print_balance:
            passinfo.addBackField('print', user_pass.print_balance, 'Print Balance', 'Your print balance is now %@.')
        if user_pass.mailbox:
            passinfo.addBackField('boxnumber', user_pass.mailbox, 'Mailbox Number')
        passinfo.addBackField('info', 'Please note that Automatic Updates must be turned on (default) to use the ID.\n\n' \
            + 'Report Feedback:\nhttps://forms.gle/6bAWYccfs9KsNAdP8\n\n' \
            + 'Created by the MOBIL-ID Team:\nAndrew Siemer, Jacob Button, Kyla Tarpey & Zach Jones\n')
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
        passfile.create(config.PASS_TYPE_CERTIFICATE_PATH, config.PASS_TYPE_CERTIFICATE_PATH, config.WWDR_CERTIFICATE_PATH, config.PEM_PASSWORD, 'passes/' + user_pass.serial_number + '.pkpass')

class JWT():
    '''
    Google Pass Object
    '''
    def __init__(self, db: Session, serial_number: str):
        # parse User data into reusable variables
        user_pass = crud.get_pass(db, serial_number)

        # Add user photo with different device resolution support
        response = requests.get(user_pass.photo_URL)
        img = Image.open(BytesIO(response.content))
        img = img.resize((113, 150), Image.ANTIALIAS)
        hero_image = Image.new(img.mode, (600, 200), (128, 20, 41))
        hero_image.paste(img, (450, 25))

        draw = ImageDraw.Draw(hero_image)
        font = ImageFont.truetype("include/google/Roboto-Regular.ttf", 34)
        draw.text((37, 84), user_pass.name, (255, 255, 255), font=font)

        hero_image.save('static/heroImg/' + serial_number + '.png')

        objectUid = str(services.VerticalType.LOYALTY).split('.')[1] + '_OBJECT_' + str(serial_number)
        # check Reference API for format of "id" (https://developers.google.com/pay/passes/reference/v1/).
        objectId = '%s.%s' % (config.ISSUER_ID, objectUid)
        self.objectJwt = services.makeSkinnyJwt(services.VerticalType.LOYALTY, config.CLASS_ID, objectId, user_pass)

    def get_link(self):
        return config.SAVE_LINK + self.objectJwt.decode('UTF-8')