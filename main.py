''' main.py: A web service for Apple PassKit 
Built as a mobile ID solution for Oklahoma Christian University '''

__author__ = "Andrew Siemer, Jacob Button, Kyla Tarpey, Zach Jones"
__copyright__ = "Copyright 2021, Team MOBIL-ID (Oklahoma Christian University)"
__version__ = "0.0.1"
__maintainer__ = "Andrew Siemer"
__email__ = "andrew.siemer@eagles.oc.edu"
__status__ = "Development"

import threading, logging # standard library
from datetime import datetime, timedelta 
from typing import Optional
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi import FastAPI, Header, Request, Response, status, Depends, BackgroundTasks, Form # 3rd party packages
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler

import include.crud as crud, include.utils as utils, include.models as models, include.schemas as schemas, config # local imports
from include.database import SessionLocal, engine

LOG_FILE = 'app.log'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
f_handler = logging.FileHandler(LOG_FILE)
f_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(f_handler)

if config.DEBUG:
    logger.setLevel(logging.DEBUG)
    app = FastAPI(
        title="MOBIL-ID Server",
        description="The MOBIL-ID Server is a web service responsible for creating, deploying, and updating passes. It tracks the pass’s complete lifecycle. When a user requests a pass, the server gets the user's data from OC’s database, creates a new pass, and signs it before delivering it to the user. It keeps a log of every pass it creates. When a user adds the pass to Apple Wallet, the pass will send a registration request to our server. The server will log the device id and pass relationship. When users data is changed, the MOBIL-ID server then knows what device to send the update push notification to. If a user deletes a pass of their device, the server will receive a request to delete the pass and it will be deleted from the server’s database and no longer receive updates.",
        version="0.0.1",
        openapi_tags = [
        {
            "name": "PassKit",
            "description": "",
            "externalDocs": {
                "description": "web service docs",
                "url": "https://developer.apple.com/library/archive/documentation/PassKit/Reference/PassKit_WebService/WebService.html",
            },
        }
        ],
        redoc_url=None
    )
else:
    app = FastAPI(docs_url=None,redoc_url=None)

models.Base.metadata.create_all(bind=engine)

def get_db():
    '''
    Create database session
    '''
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
PassKit Web Service
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

@app.post("/v1/devices/{device_id}/registrations/{pass_type}/{serial_number}", tags=["PassKit"])
def register(request: Request, body: dict, device_id: str, pass_type: str, serial_number: str, db: Session = Depends(get_db)):
    '''
    Registering a Device to Receive Push Notifications for a Pass
    '''
    
    auth_token = str(request.headers.get('Authorization')).replace('ApplePass ', '')
    push_token = str(body['pushToken'])

    logger.debug('Pass registration request from device (' + device_id + ')')
    if crud.get_pass(db, serial_number, auth_token):
        # if pass exists in database with same serial number & matching auth_token
        if not crud.get_device(db, device_id): 
            # if no device with same device_id exists
            crud.add_device(db, device_id, push_token)
        if not crud.get_registration(db, device_id, serial_number): 
            # if the device is not already registered
            # for a pass with same serial_number
            crud.add_registration(db, device_id, serial_number)
            # if registration succeeds, returns HTTP status 201.
            response = Response(status_code=201)
            logger.info('New user registered (' + serial_number + ')')
        else:
            # if the serial number is already registered for 
            # this device, returns HTTP status 200.
            response = Response(status_code=200)
            logger.debug('Existing user registered (' + serial_number + ')')
    else:
        # if the request is not authorized, returns HTTP status 401
        response = Response(status_code=401)
        logger.debug('Pass registration request from device (' + device_id + ') not authorized (' + auth_token + ')')
    
    return response

@app.get("/v1/devices/{device_id}/registrations/{pass_type}", status_code=200, tags=["PassKit"])
def get_passes(request: Request, device_id: str, pass_type: str, passesUpdatedSince: str = None, db: Session = Depends(get_db)):
    '''
    Getting the Serial Numbers for Passes Associated with a Device
    '''

    logger.debug('Device (' + device_id + ') asked for list of registered passes')
    if crud.get_registration_by_device(db, device_id):
        # if there is a registration for the device, 
        # get the serial numbers registered for & 
        # only get passesUpdatedSince if tag is present in request     
        last_updated, serial_numbers = crud.get_pass_list_by_device(db, device_id, passesUpdatedSince)
        if serial_numbers:
            # if there were matching passes, returns HTTP status 200
            # with a JSON dictionary with the following keys and value
            response = {'lastUpdated': str(last_updated), 'serialNumbers': serial_numbers}
            logger.debug('Device (' + device_id + ') with registrations (' + str(serial_numbers) + ') was last updated at ' + str(last_updated))
        else:
            # if there are no matching passes, 
            # returns HTTP status 204
            response = Response(status_code=204)
            logger.debug('Device (' + device_id + ') has no current registrations')
    else:
        # if there are no matching passes, 
        # returns HTTP status 204
        response = Response(status_code=204)
        logger.debug('Device (' + device_id + ') has no current registrations')
    
    return response

@app.get("/v1/passes/{pass_type}/{serial_number}", status_code=200, tags=["PassKit"])
def send_passes(request: Request, pass_type: str, serial_number: str, db: Session = Depends(get_db)):
    '''
    Getting the Latest Version of a Pass
    '''

    auth_token = str(request.headers.get('Authorization')).replace('ApplePass ', '')
    if_modified_since = request.headers.get('if-modified-since')        

    logger.debug('Device asked for latest version of pass (' + serial_number + ') with authorization (' + auth_token + ')')

    db_pass = crud.get_pass(db, serial_number, auth_token)
    if db_pass:
        # if pass exists and auth_token matches
        if if_modified_since:
            # if if_modified_since tag exists, convert to datetime obj to compare
            if_modified_since = datetime.strptime(if_modified_since,'%a, %d %b %Y %H:%M:%S %Z')
            # if the pass was updated after if_modified_since,
            # send the new version of the pass as a response
            if db_pass.last_update > if_modified_since:
                # force update on manual database change -> 
                # crud.force_pass_update(db, db_pass.serial_number)
                response = utils.get_pass_file(db, db_pass.serial_number)
                logger.debug('Updated pass (' + serial_number + ') returned to device.')
            else:
                # if the pass has not changed, return HTTP status code 304 
                response = Response(status_code=304)
                logger.debug('Pass (' + serial_number + ') has not changed.')
        else:
            # if device asks for pass unconditionally,
            # respond with the current pass file
            response = utils.get_pass_file(db, db_pass.serial_number)
            logger.debug('Pass (' + serial_number + ') returned unconditionally')
    else:
        # if the request is not authorized, returns HTTP status 401
        response = Response(status_code=401)
        logger.debug('Pass (' + serial_number + ') not authorized (' + auth_token + ')')

    return response

@app.delete("/v1/devices/{device_id}/registrations/{pass_type}/{serial_number}", tags=["PassKit"])
def delete(request: Request, device_id: str, pass_type: str, serial_number: str, db: Session = Depends(get_db)):
    '''
    Unregistering a Device
    '''

    auth_token = str(request.headers.get('Authorization')).replace('ApplePass ', '')

    logger.debug('Device (' + device_id + ') deleted pass (' + serial_number + ') with authorization (' + auth_token + ')')

    db_pass = crud.get_pass(db, serial_number, auth_token)
    if db_pass:
        # if pass exists and auth_token matches,
        # delete device registration for pass
        crud.delete_registration(db, device_id, serial_number)
        if not crud.get_registrations_by_device(db, device_id):
            # if not more passes exist for device,
            # delete device and push_token from device table
            crud.delete_device(db, device_id)
        # if disassociation succeeds, returns HTTP status 200
        response = Response(status_code=200)
        logger.info('Pass (' + serial_number + ') deleted from device (' + device_id + ') ')
    else:
        if config.DEBUG:
             # if in debug mode, force delete
            response = Response(status_code=200)
            logger.debug('Delete request from device (' + device_id + ') not authorized (' + auth_token + ') but allowed (DEBUG)')
        else:
             # if the request is not authorized, returns HTTP status 401
            response = Response(status_code=401)
            logger.debug('Delete request from device (' + device_id + ') not authorized (' + auth_token + ')')

    return response

@app.post("/v1/log", tags=["PassKit"])
def log(message: dict):
    '''
    Logs Errors from Apple PassKit Service
    '''
    
    response = Response(status_code=200)
    logger.info(message['logs'][0])
    
    return response

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
MOBIL-ID Front-End Web Service
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

# location of web service static files and html templates
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates') 

@app.get("/", tags=["Registration"])
def root(request: Request):
    '''
    Web Service Login Page (root)
    '''
    return templates.TemplateResponse('index.html', {'request': request})

@app.post("/", tags=["Registration"])
def submit(request: Request, idNum: str = Form(...), idPin: str = Form(...), db: Session = Depends(get_db)):
    '''
    Login Sumbitted, Validates User & Creates Pass
    '''

    # get user data from form
    entered_id_num = idNum
    entered_id_pin = idPin

    logger.debug('Registration submitted for ID (' + entered_id_num + ') with Pin (' +  entered_id_pin + ')')
    if entered_id_num in config.WHITELIST:    
        if utils.input_validate(entered_id_num, entered_id_pin): 
            # if user form data passes server-side validation,
            # check for existing pass
            db_pass = crud.get_pass(db, entered_id_num)
            if not db_pass:
                # if pass for user does not exist,
                # check for vaild User though OC
                user = schemas.User(entered_id_num, entered_id_pin)
                if user.is_valid(): 
                    # add user_pass to database
                    db_pass = crud.add_pass(db, user)
                    # create pass for given user
                    schemas.Pkpass(db, db_pass.serial_number)
                    google = schemas.JWT(db, db_pass.serial_number)

                    # respond with success page with Add to Apple Wallet button
                    response = templates.TemplateResponse('success.html', \
                        {'request': request, 'pass_hash': db_pass.pass_hash, 'jwt': google.get_link()})
                    logger.info('Pass created for ID (' + entered_id_num + ')')
                else:
                    # user not valid through OC,
                    # return login page with feedback
                    del user
                    response = templates.TemplateResponse('index.html', \
                        {'request': request, 'feedback': 'The ID Number and ID Card Pin Number entered do not match. Please try again.', 'entered_id': entered_id_num})
                    logger.debug('Registration unsuccessful for ID (' + entered_id_num + ') with Pin (' +  entered_id_pin + ')')
            elif db_pass.id_pin == entered_id_pin:
                google = schemas.JWT(db, db_pass.serial_number)

                # pass for user already exists and login is correct,
                # respond with success page with Add to Apple Wallet button
                response = templates.TemplateResponse('success.html', \
                    {'request': request, 'pass_hash': db_pass.pass_hash, 'jwt': google.get_link()})
                logger.debug('Existing user successful request for ID (' + entered_id_num + ')')
            else:
                # pass for user already exists but login is incorrect,
                # user not valid through server quick validation
                response = templates.TemplateResponse('index.html', \
                    {'request': request, 'feedback': 'The ID Number and ID Card Pin Number entered do not match. Please try again.', 'entered_id': entered_id_num})
                logger.debug('Registration unsuccessful for ID (' + entered_id_num + ') with Pin (' +  entered_id_pin + ')')
        else:
            # user not valid through server quick validation
            response = templates.TemplateResponse('index.html', \
                {'request': request, 'feedback': 'The ID Number and ID Card Pin Number entered do not match. Please try again.', 'entered_id': entered_id_num})
            logger.debug('Registration unsuccessful for ID (' + entered_id_num + ') with Pin (' +  entered_id_pin + ')')
    else:
        # entered ID num is not on whitelist
        response = templates.TemplateResponse('index.html', \
            {'request': request, 'beta': 'The beta-testing program is currently invite-only.'})
        logger.debug('Registration unsuccessful for ID (' + entered_id_num + ') with Pin (' +  entered_id_pin + ')')
        
    return response

@app.post("/download/{pass_hash}", status_code=200, tags=["Registration"])
def download(request: Request, pass_hash: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    '''
    User can Download Pass
    '''

    # user clicks the Add to Apple Wallet button
    db_pass = crud.get_pass_by_hash(db, pass_hash)
    if db_pass:
        # if a pass matching the request is found,
        # returns the matching pass file
        response = utils.get_pass_file(db, db_pass.serial_number)
        logger.info('Pass (' + db_pass.serial_number   + ') downloaded with hash (' + pass_hash + ')')
    else:
        # no matching pass found,
        # returns HTML status no matching data
        response = Response(status_code=204)
        logger.debug('No pass with hash (' + pass_hash + ')')
    
    return response

@app.get("/team", tags=["Fun"])
def team(request: Request):
    '''
    Returns team.html webpage
    '''
    return templates.TemplateResponse('team.html', {'request': request})

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc):
    '''
    Redirect all 404 traffic to homepage
    '''
    return RedirectResponse('/')

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
MOBIL-ID Back-End Web Service
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

@app.get("/scan/{pass_hash}", status_code=200, tags=["Reader"])
async def scan(pass_hash: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    '''
    Scan event converts QR data to serial_number
    '''

    logger.debug('Scan recieved for hash (' + pass_hash + ')')
    db_pass = crud.get_pass_by_hash(db, pass_hash)
    if db_pass:
        # if pass exists with matching pash_hash,
        # respond with the corresponding serial_number
        response = db_pass.serial_number
        # start background task to update pass with new pass_hash
        background_tasks.add_task(utils.force_pass_update, db, response)
        logger.info('Pass (' + db_pass.serial_number + ') scanned successfully')
    else:
        # no matching pass found,
        # returns HTML status no matching data
        response = Response(status_code=204)
        logger.debug('Scan unsuccessful for hash (' + pass_hash + ')')

    return response

@app.get("/{client}/update/{serial_number}", tags=["Client Updates"])
async def update(client: str, serial_number: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    '''
    Client notifies server of updated user data
    '''
    logger.debug('Client (' + client + ') notified server that ID (' + serial_number + ') has updated')
    db_pass = crud.get_pass(db, serial_number)
    if db_pass:
        # if a pass exists for user,
        # start background pass update task
        background_tasks.add_task(utils.update_pass, db, serial_number)
        response = Response(status_code=200)
        logger.info('Pass (' + serial_number + ') updated by client (' + client + ') request')
    else:
        # no matching pass found,
        # returns HTML status no matching data
        response = Response(status_code=204)
        logger.debug('Client (' + client + ') notified server about update for a non-existing user')
    
    return response

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Scheduled Tasks
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

sched = BackgroundScheduler(daemon=True)
sched.start()

@sched.scheduled_job('interval', start_date=str(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)), days=1)
def batch_update_all():
    '''
    Updates every pass in database at midnight each day
    '''
    logger.info('Starting batch update proccess')

    db = SessionLocal()
    pass_list = crud.get_all_passes(db)

    for serial_number in pass_list:
        logger.debug('Trying to update pass (' + serial_number + ')')
        utils.update_pass(db,serial_number)

    db.close()
    logger.info('Finished batch update proccess')

@sched.scheduled_job('interval', start_date=str(datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)), days=1)
def morning_brief():
    '''
    Sends a morning brief with all server output at 7:0:0 daily
    '''
    utils.send_notification('Morning Brief', utils.get_log(LOG_FILE))

@sched.scheduled_job('interval', start_date=str(datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)), days=1)
def nightly_brief():
    '''
    Sends a nightly brief with all server output at 19:0:0 daily
    '''
    utils.send_notification('Nightly Brief', utils.get_log(LOG_FILE))

@app.on_event("shutdown")
def shutdown_event():
    global sched
    sched.shutdown()

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Development Tools for Web Service
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

@app.get("/reader", tags=["Test"])
def reader(request: Request):
    '''
    Returns reader.html webpage
    '''
    response = templates.TemplateResponse('reader.html', {'request': request})

    return response

@app.post("/reader", tags=["Test"])
def reader_post(request: Request, idNum: str = Form(...), db: Session = Depends(get_db)):
    '''
    Returns user data on form submit
    '''
    serial_number = idNum

    user = crud.get_pass(db, serial_number)
    response = templates.TemplateResponse('reader.html', \
        {'request': request, 'name': user.name, 'id_num': user.serial_number, 'photo_URL': user.photo_URL})
    
    return response
