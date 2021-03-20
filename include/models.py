'''
models.py: Create SQLAlchemy models from the Base class
'''

from sqlalchemy import Column, Integer, String, DateTime

from include.database import Base

class Device(Base):
    __tablename__ = "device"

    device_id = Column(String, primary_key=True, index=True) # device library identifier
    push_token = Column(String)
    
class Pass(Base):
    __tablename__ = "passes"

    pass_type = Column(String) # pass type ID
    serial_number = Column(String, primary_key=True, index=True)
    last_update = Column(DateTime)
    pass_hash = Column(String, unique=True, index=True)

    auth_token = Column(String)
    name = Column(String)
    photo_URL = Column(String)
    eagle_bucks = Column(String)
    meals_remaining = Column(String)
    kudos_earned = Column(String)
    kudos_required = Column(String)
    id_pin = Column(String)
    print_balance = Column(String)
    mailbox = Column(String)

class Registration(Base):
    __tablename__ = "registrations"

    index =  Column(Integer, primary_key=True)
    device_id = Column(String) # device library identifier
    serial_number = Column(String)
