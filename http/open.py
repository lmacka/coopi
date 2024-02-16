#!/usr/bin/env python3

import os
import time
import json
import RPi.GPIO as GPIO
import automationhat
import logging
import board
#import adafruit_bh1750

############ CONFIG ###############
statefile = 'http/state.json'
actuateTime = 10
logfile = 'logs/actuator.log'

###################################

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#logging.basicConfig(level=logging.INFO)

### Functions

if automationhat.is_automation_hat():
    automationhat.light.power.write(1)

def actuateUp():
    automationhat.light.comms.on()
    automationhat.relay.one.on()
    automationhat.relay.two.off()
    time.sleep(actuateTime)
    automationhat.light.comms.off()

#########################################


with open(statefile) as json_file:
    json_data = json.load(json_file)
    doorstate = json_data['state']

logging.info('Opening door')
if ( doorstate == 'closed' ):
    with open(statefile, 'w') as f:
        json.dump({'state': 'open'}, f, ensure_ascii=False)
    logging.info('State written')
    actuateUp()
else:
    logging.info("Already open")


