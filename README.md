# A Raspberry Pi in a Chicken Coop

## Current state
Alpha, by far. It's currently running reliably in the coop but is messy, contains excess test code and probably would be shunned by other chickens.

## Objectives
 - Provide web interface with camera and controls 
 - Open/close door using 12v actuator both on-demand and on a timer
 - Monitor chicken activity using rpi camera
 - Monitor ambient light levels, trigger door close on low light
 - Monitor temperature and humidity

## Future Goals
 - Utilise a HD camera, TPU and an LLM to recognise individual chickens
 - Use the above feature to confirm when everyone's gone to bed, then close the door
 - If a chicken is AWOL, send a push notification
 - Detect and alert on predators
 - Detect hierarchical squabbles and play classical music to calm the flock (heh)


## Notes
* Install poetry:  ``curl -sSL https://install.python-poetry.org | python3 -``
