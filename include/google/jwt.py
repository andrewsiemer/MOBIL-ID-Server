'''
jwt.py: 
'''
import time

# for jwt signing. see https://google-auth.readthedocs.io/en/latest/reference/google.auth.jwt.html#module-google.auth.jwt
from google.auth import crypt as cryptGoogle
from google.auth import jwt as jwtGoogle

import config

#############################
#
# class that defines JWT format for a Google Pay Pass.
#
# to check the JWT protocol for Google Pay Passes, check:
# https://developers.google.com/pay/passes/reference/s2w-reference#google-pay-api-for-passes-jwt
#
# also demonstrates RSA-SHA256 signing implementation to make the signed JWT used
# in links and buttons. Learn more:
# https://developers.google.com/pay/passes/guides/get-started/implementing-the-api/save-to-google-pay
#
#############################

class googlePassJwt:
  def __init__(self):
    self.audience = config.AUDIENCE
    self.type = config.JWT_TYPE
    self.iss = config.SERVICE_ACCOUNT_EMAIL_ADDRESS
    self.origins = config.ORIGINS
    self.iat = int(time.time())
    self.payload = {}
    
    # signer for RSA-SHA256. Uses same private key used in OAuth2.0
    self.signer = cryptGoogle.RSASigner.from_service_account_file(config.SERVICE_ACCOUNT_FILE)

  def addLoyaltyClass(self, resourcePayload):
    self.payload.setdefault('loyaltyClasses',[])
    self.payload['loyaltyClasses'].append(resourcePayload)

  def addLoyaltyObject(self, resourcePayload): 
    self.payload.setdefault('loyaltyObjects',[])
    self.payload['loyaltyObjects'].append(resourcePayload)

  def generateUnsignedJwt(self):
    unsignedJwt = {}
    unsignedJwt['iss'] = self.iss
    unsignedJwt['aud'] = self.audience
    unsignedJwt['typ'] = self.type
    unsignedJwt['iat'] = self.iat
    unsignedJwt['payload'] = self.payload
    unsignedJwt['origins'] = self.origins

    return unsignedJwt

  def generateSignedJwt(self):
    jwtToSign = self.generateUnsignedJwt()
    signedJwt = jwtGoogle.encode(self.signer, jwtToSign)

    return signedJwt