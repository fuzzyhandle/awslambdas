# -*- coding: utf-8 -*-
import boto3
import json
import time
import datetime 



TIMEZONEOFFSET = 5 * 3600 + 30 * 60
THINGNAME = 'esp8266_D42709'
DEFAULT_SLEEP_INTERVAL = 60*60

def redundant_water_off (desiredstate):
    desiredstate["waternow"] = False
    print ("We need to ensure pump is OFF")
    push_desired_state (desiredstate)
    
def push_desired_state (desiredstate):
    mypayload = json.dumps(
      {"state":{"desired":desiredstate}}
    )
    client = boto3.client('iot-data')
    response = client.update_thing_shadow(thingName= THINGNAME,payload=mypayload)
    
def dologic(stateobj):
    
    nowepoch = int(time.time())

    secondsfrommidnight = (nowepoch +TIMEZONEOFFSET) % 86400
    print ("Seconds from midnight is {0}".format(secondsfrommidnight))
    
    desiredstate =  stateobj['state']['desired']
    reportedstate =  stateobj['state']['reported']
    
    starttimefrommidnight = desiredstate.get ("dailystarttime",0)
    endtimefrommidnight = desiredstate.get ("dailyendtime",0)
    desiredstate["sleepinterval"] = DEFAULT_SLEEP_INTERVAL
    
    if not desiredstate.get("enabled", False):
      print ("System is not Armed. Doing NOOP")
      redundant_water_off(desiredstate)
      return
        
    if (secondsfrommidnight < starttimefrommidnight):
      print ("Its too early for irrigation")
      redundant_water_off(desiredstate)
      return
  
    if (secondsfrommidnight > endtimefrommidnight):
      print ("Its too late for irrigation")
      redundant_water_off(desiredstate)
      return

    lastwatering = reportedstate.get ("lastwatering",0)
    dosageinterval = desiredstate.get ("dosageinterval",10800)
    
    print ("Last Watering on {0}. Dosage Interval is {1}. Current Time is {2}".format(lastwatering,dosageinterval,nowepoch))
    
    if nowepoch >= lastwatering + dosageinterval:
      #Its time for action
      print ("We need to start the pump")
      desiredstate["waternow"] = True
      push_desired_state(desiredstate)
      client = boto3.client('iot-data')
      print (stateobj)
      response = client.update_thing_shadow(thingName= THINGNAME,payload=mypayload)
    else:
      deltatonextwatering = ( lastwatering + dosageinterval) - nowepoch
      desiredstate["sleepinterval"] = deltatonextwatering
      push_desired_state(desiredstate)
      
      
def handler(event, context):
    
    #client = boto3.client('iot',region_name="us-west-2")
    #things = client.list_things()
    #print (len(things))
    
    client = boto3.client('iot-data')
    response = client.get_thing_shadow(thingName= THINGNAME)

    streamingBody = response["payload"]
    jsonState = json.loads(streamingBody.read())
    
    dologic (jsonState)
    
    # Your code goes here!
    #e = event.get('e')
    #pi = event.get('pi')
    #print ("Hello world {0}".format (e + pi))
    #return e + pi