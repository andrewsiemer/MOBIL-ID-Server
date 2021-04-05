'''
resourceDefinitions.py: 
'''
import datetime

from google.oauth2 import service_account # pip install google-auth

def makeLoyaltyClassResource(classId):
  # Define the resource representation of the Class
  # values should be from your DB/services; here we hardcode information

  payload = {}

  # below defines an Loyalty class. For more properties, check:
  # https://developers.google.com/pay/passes/reference/v1/loyaltyclass/insert
  # https://developers.google.com/pay/passes/guides/pass-verticals/loyalty/design

  payload = {
    # required fields
    "id": classId,
    "hexBackgroundColor" : "#801429",
    "issuerName": "Oklahoma Christian University",
    "programName": "Mobile Pass",
    "reviewStatus": "underReview",
    # optional
    "programLogo": {
        "kind": "walletobjects#image",
        "sourceUri": {
            "kind": "walletobjects#uri",
            "uri": "https://i.imgur.com/bLZrZIl.png"
        }
    },
    "classTemplateInfo": {
        "cardTemplateOverride": {
            "cardRowTemplateInfos": [{
                "threeItems": {
                    "startItem": {
                        "firstValue": {
                            "fields": [{
                                "fieldPath": "object.textModulesData['myfield1']"
                            }]
                        }
                    },
                    "middleItem": {
                        "firstValue": {
                            "fields": [{
                                "fieldPath": "object.textModulesData['myfield2']"
                            }]
                        }
                    },
                    "endItem": {
                        "firstValue": {
                            "fields": [{
                                "fieldPath": "object.textModulesData['myfield3']"
                            }]
                        }
                    },
                }
            }],
        }
    },
    "locations": [{
        "kind": "walletobjects#latLongPoint",
        "latitude": 35.613306,
        "longitude": -97.467825,
        "label" : "lab"
      },    
      {
        "kind": "walletobjects#latLongPoint",
        "latitude": 35.611219,
        "longitude": -97.467255,
        "label" : "garvey"
      },
      {
        "kind": "walletobjects#latLongPoint",
        "latitude": 35.61201,
        "longitude": -97.46850,
        "label" : "brew"
      },
      {
        "kind": "walletobjects#latLongPoint",
        "latitude": 35.6115,
        "longitude": -97.4695,
        "label" : "branch"
    }] 
  }
 
  return payload

def makeLoyaltyObjectResource(classId, objectId, user):
  # Define the resource representation of the Object
  # values should be from your DB/services; here we hardcode information

  payload = {}
  # below defines an loyalty object. For more properties, check:
  # https://developers.google.com/pay/passes/reference/v1/loyaltyobject/insert
  # https://developers.google.com/pay/passes/guides/pass-verticals/loyalty/design

  payload = {
    # required fields
    "id" : objectId,
    "classId" : classId,
    "state" : "active",
    # optional
    "accountId": user.serial_number,
    "accountName": user.name,
    "barcode": {
        "alternateText": user.serial_number,
        "type": 'QR_CODE',
        "value": user.serial_number
    },
        "heroImage": {
            "kind": "walletobjects#image",
            "sourceUri": {
                "uri": "https://i.imgur.com/I6p54as.png",
                "image":  'asdasdas',
                "label": "heroImg"
            }
        },
    
    "textModulesData": [
        {
            "header": "Eagle Bucks",
            "body": "$" + user.eagle_bucks,
            "id": "myfield1"
        },
        {
            "header": "Meals Remaining",
            "body": user.meals_remaining,
            "id": "myfield2"
        },
        {
            "header": "Kudos",
            "body": user.kudos_earned + "/" + user.kudos_required,
            "id": "myfield3"
        }
    ],  
    "infoModuleData": {
        "labelValueRows": [{
            "columns": [{
                "label": "ID Pin",
                "value": user.id_pin
            }, 
            {
                "label": "Print Balance",
                "value": user.print_balance
            }]
        }, 
        {
            "columns": [{
                "label": "Mailbox Number",
                "value": user.mailbox
            }]
        }],
        "showLastUpdateTime": "true"
    },
    
    "locations": [{
        "kind": "walletobjects#latLongPoint",
        "latitude": 35.613306,
        "longitude": -97.467825,
        "label" : "lab"
      },    
      {
        "kind": "walletobjects#latLongPoint",
        "latitude": 35.611219,
        "longitude": -97.467255,
        "label" : "garvey"
      },
      {
        "kind": "walletobjects#latLongPoint",
        "latitude": 35.61201,
        "longitude": -97.46850,
        "label" : "brew"
      },
      {
        "kind": "walletobjects#latLongPoint",
        "latitude": 35.6115,
        "longitude":-97.4695,
        "label" : "branch"
    }]  
        
  }
  return payload
