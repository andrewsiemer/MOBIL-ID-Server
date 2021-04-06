from enum import Enum

import include.google.restMethods as restMethods
import include.google.resourceDefinitions as resourceDefinitions
import include.google.jwt as jwt

import config

EXISTS_MESSAGE = "No changes will be made when saved by link. To update info, use update() or patch(). For an example, see https://developers.google.com/pay/passes/guides/get-started/implementing-the-api/engage-through-google-pay#update-state\n"
NOT_EXIST_MESSAGE = "Will be inserted when user saves by link/button for first time\n"

#############################
#
#  These are services that you would expose to front end so they can generate save links or buttons.
#
#  Depending on your needs, you only need to implement 1 of the services.
#
#############################

#############################
#
#
#  See all the verticals: https://developers.google.com/pay/passes/guides/overview/basics/about-google-pay-api-for-passes
#
#############################
class VerticalType(Enum):
  OFFER = 1
  EVENTTICKET = 2
  FLIGHT = 3     # also referred to as Boarding Passes
  GIFTCARD = 4
  LOYALTY = 5
  TRANSIT = 6

#############################
#
#  Output to explain various status codes from a get API call
#
#  @param requests.Response getCallResponse - response from a get call
#  @param String idType - identifier of type of get call.  "object" or "class"
#  @param String id - unique identifier of Pass for given idType
#  @param String checkClassId - optional. ClassId to check for if objectId exists, and idType == 'object'
#  @return void
#
#############################
def handleGetCallStatusCode(getCallResponse, idType, id, checkClassId=None):
  if getCallResponse.status_code == 200:  # id resource exists for this issuer account
    #print('%sId: (%s) already exists. %s' % (idType, id, EXISTS_MESSAGE))

    # for object get, do additional check
    if idType == "object":
      # check if object's classId matches target classId
      classIdOfObjectId = getCallResponse.json()['classId']
      if classIdOfObjectId != checkClassId and checkClassId is not None:
        raise ValueError('the classId of inserted object is (%s). It does not match the target classId (%s). The saved object will not have the class properties you expect.' % (classIdOfObjectId, checkClassId))
  elif getCallResponse.status_code == 404:  # id resource does not exist for this issuer account
    pass #print('%sId: (%s) does not exist. %s' % (idType, id , NOT_EXIST_MESSAGE) )
  else:
    raise ValueError('Issue with getting %s.' % (idType), getCallResponse.text)

  return

#############################
#
#  Output to explain various status codes from a insert API call
#
#  @param requests.Response insertCallResponse - response from an insert call
#  @param String idType - identifier of type of get call.  "object" or "class"
#  @param String id - unique identifier of Pass for given idType
#  @param String checkClassId - optional. ClassId to check for if objectId exists, and idType == 'object'
#  @param VerticalType verticalType - optional. VerticalType to fetch ClassId of existing objectId.
#  @return void
#
#############################
def handleInsertCallStatusCode(insertCallResponse, idType, id,objectResourcePayload, checkClassId=None, verticalType=None):
  if insertCallResponse.status_code == 200:
    pass #print('%sId (%s) insertion success!\n' % (idType, id) )
  elif insertCallResponse.status_code == 409:  # id resource exists for this issuer account
    #print('%sId: (%s) already exists. %s' % (idType, id, EXISTS_MESSAGE))
    
    # for object insert, do additional check
    if idType == "object":
      getCallResponse = None
      # get existing object Id data
      getCallResponse = restMethods.getObject(verticalType, id) # if it is a new object Id, expected status is 409
      if getCallResponse != 409:
        restMethods.updatePass(verticalType, id, objectResourcePayload)

      # check if object's classId matches target classId
      classIdOfObjectId = getCallResponse.json()['classId']
      if classIdOfObjectId != checkClassId and checkClassId is not None:
        raise ValueError('the classId of inserted object is (%s). It does not match the target classId (%s). The saved object will not have the class properties you expect.' % (classIdOfObjectId, checkClassId))
  else:
    raise ValueError('%s insert issue.' % (idType), insertCallResponse.text)

  return

def makeSkinnyJwt(verticalType, classId, objectId, user):

  signedJwt = None
  classResourcePayload = None
  objectResourcePayload = None
  classResponse = None
  objectResponse = None
  
  try:
    # get class definition and object definition
    classResourcePayload, objectResourcePayload = getClassAndObjectDefinitions(verticalType, classId, objectId, classResourcePayload, objectResourcePayload, user)

    #print('\nMaking REST call to insert class: (%s)' % (classId))
    # make authorized REST call to explicitly insert class into Google server.
    # if this is successful, you can check/update class definitions in Merchant Center GUI: https://pay.google.com/gp/m/issuer/list
    classResponse = restMethods.insertClass(verticalType, classResourcePayload)

    #print('\nMaking REST call to insert object')
    # make authorized REST call to explicitly insert object into Google server.
    objectResponse = restMethods.insertObject(verticalType, objectResourcePayload)

    # continue based on insert response status. Check https://developers.google.com/pay/passes/reference/v1/statuscodes
    # check class insert response. Will print out if class insert succeeds or not. Throws error if class resource is malformed.
    handleInsertCallStatusCode(classResponse, "class", classId, objectResourcePayload, None, None)

    # check object insert response. Will print out if object insert succeeds or not. Throws error if object resource is malformed, or if existing objectId's classId does not match the expected classId
    handleInsertCallStatusCode(objectResponse, "object", objectId, objectResourcePayload, classId, verticalType)

    # put into JSON Web Token (JWT) format for Google Pay API for Passes
    googlePassJwt = jwt.googlePassJwt()
    
    # only need to add objectId in JWT because class and object definitions were pre-inserted via REST call
    loadObjectIntoJWT(verticalType, googlePassJwt, {"id": objectId})

    # sign JSON to make signed JWT
    signedJwt = googlePassJwt.generateSignedJwt()

  except ValueError as err:
      print(err.args)

  # return "skinny" JWT. Try putting it into save link.
  # See https://developers.google.com/pay/passes/guides/get-started/implementing-the-api/save-to-google-pay#add-link-to-email
  return signedJwt


#############################
#
#  Gets a passes's class and object definitions and loads into payload objects
#
#  @param VerticalType verticalType - type of pass
#  @param String classId - unique identifier for an class
#  @param String classResourcePayload - payload for the class
#  @param String objectResourcePayload - payload for the object
#
#############################
def getClassAndObjectDefinitions(verticalType, classId, objectId, classResourcePayload, objectResourcePayload, user):
  # get class definition and object definition

  classResourcePayload = resourceDefinitions.makeLoyaltyClassResource(classId)
  objectResourcePayload = resourceDefinitions.makeLoyaltyObjectResource(classId, objectId, user)

  return classResourcePayload, objectResourcePayload

#############################
#
#  Loads an object into a JWT
#
#  @param VerticalType verticalType - type of pass
#  @param googlePassJwt googlePassJwt - JWT object
#  @param String objectResourcePayload - object to insert
#
#############################
def loadObjectIntoJWT(verticalType, googlePassJwt, objectResourcePayload):
  if verticalType == VerticalType.FLIGHT:
    googlePassJwt.addFlightObject(objectResourcePayload)
  elif verticalType == VerticalType.EVENTTICKET:
    googlePassJwt.addEventTicketObject(objectResourcePayload)
  elif verticalType == VerticalType.GIFTCARD:
    googlePassJwt.addGiftcardObject(objectResourcePayload)
  elif verticalType == VerticalType.LOYALTY:
    googlePassJwt.addLoyaltyObject(objectResourcePayload)
  elif verticalType == VerticalType.OFFER:
    googlePassJwt.addOfferObject(objectResourcePayload)        
  elif verticalType == VerticalType.TRANSIT:
    googlePassJwt.addTransitObject(objectResourcePayload)

#############################
#
#  Loads a class into a JWT
#
#  @param VerticalType verticalType - type of pass
#  @param googlePassJwt googlePassJwt - JWT object
#  @param String classResourcePayload - class to insert
#
#############################
def loadClassIntoJWT(verticalType, googlePassJwt, classResourcePayload):
  if verticalType == VerticalType.FLIGHT:
    googlePassJwt.addFlightClass(classResourcePayload)
  elif verticalType == VerticalType.EVENTTICKET:
    googlePassJwt.addEventTicketClass(classResourcePayload)
  elif verticalType == VerticalType.GIFTCARD:
    googlePassJwt.addGiftcardClass(classResourcePayload)
  elif verticalType == VerticalType.LOYALTY:
    googlePassJwt.addLoyaltyClass(classResourcePayload)
  elif verticalType == VerticalType.OFFER:
    googlePassJwt.addOfferClass(classResourcePayload)       
  elif verticalType == VerticalType.TRANSIT:
    googlePassJwt.addTransitClass(classResourcePayload)
