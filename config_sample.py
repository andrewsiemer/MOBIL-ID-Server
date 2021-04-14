''' config.py: Reusable settings global to the program '''

DEBUG = True

WEB_SERVICE_URL=''

# OC
OC_SHARED_SECRET=''

# Apple
PASS_TYPE_IDENTIFIER=''
TEAM_IDENTIFIER=''
PASS_TYPE_CERTIFICATE_PATH='certificates/pass.pem'
PEM_PASSWORD = ''
WWDR_CERTIFICATE_PATH='certificates/wwdr.pem'

# Google
ISSUER_ID = '' # Identifier of Google Pay API for Passes Merchant Center
SAVE_LINK = 'https://pay.google.com/gp/v/save/'
VERTICAL_TYPE = 'VerticalType.LOYALTY'
CLASS_ID = ""
SERVICE_ACCOUNT_EMAIL_ADDRESS = ''
SERVICE_ACCOUNT_FILE = 'certificates/...json' # Path to file with private key and Google credential config
ORIGINS = [WEB_SERVICE_URL]
# Constants that are application agnostic. Used for JWT
AUDIENCE = 'google'
JWT_TYPE = 'savetoandroidpay'
SCOPES = ['https://www.googleapis.com/auth/wallet_object.issuer']

# Server Notifications
EMAIL_PORT = 465  # For SSL
SMTP_SERVER = 'smtp.gmail.com'
SENDER_EMAIL = ''
RECEIVER_EMAIL = ['',] 
EMAIL_PASSWORD = ''

# Beta Testing
WHITELIST = ['',]
