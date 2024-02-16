#!/usr/bin/env python3

import os
import time
import json
import RPi.GPIO as GPIO
import automationhat
import logging
import board
import adafruit_bh1750

############ CONFIG ###############
statefile = 'http/state.json'
actuateTime = 10
logfile = 'logs/actuator.log'

###################################

#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.INFO)

### Functions

if automationhat.is_automation_hat():
    automationhat.light.power.write(1)

def actuateDown():
    automationhat.light.comms.on()
    # Down
    automationhat.relay.one.off()
    automationhat.relay.two.on()
    time.sleep(actuateTime)
    automationhat.light.comms.off()

#########################################


with open(statefile) as json_file:
    json_data = json.load(json_file)
    doorstate = json_data['state']

logging.info('Closing door')
if ( doorstate == 'open' ):
    with open(statefile, 'w') as f:
        json.dump({'state': 'closed'}, f, ensure_ascii=False)
    logging.info('State written')
    actuateDown()
else:
    logging.info("Already closed")


