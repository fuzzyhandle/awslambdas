# -*- coding: utf-8 -*-
import boto3
import json
import time
import datetime 

THINGNAMES = ['esp8266_2BC7A5']

TIMEZONEOFFSET = 5 * 3600 + 30 * 60
DEFAULT_SLEEP_INTERVAL = 60*60

DESIRED_KEY = "desired"
REPORTED_KEY = "reported"

def redundant_water_off (desiredstate,thingname):
    desiredstate["waternow"] = False
    print ("We need to ensure pump is OFF")
    push_state (DESIRED_KEY, desiredstate,thingname)
    
def push_state (statekey, state,thingname):
    mypayload = json.dumps(
      {"state":{statekey:state}}
    )
    client = boto3.client('iot-data')
    response = client.update_thing_shadow(thingName= thingname,payload=mypayload)
    
def dologic(stateobj,thingname):
    
    nowepoch = int(time.time())
    nowepochinlocaltime = nowepoch +TIMEZONEOFFSET

    secondsfrommidnight = (nowepochinlocaltime) % 86400
    print ("Seconds from midnight is {0}".format(secondsfrommidnight))
    
    desiredstate =  stateobj['state']['desired']
    reportedstate =  stateobj['state']['reported']
    metadata =  stateobj['metadata']
    print (metadata)

    starttimefrommidnight = desiredstate.get ("dailystarttime",0)
    endtimefrommidnight = desiredstate.get ("dailyendtime",0)
    desiredstate["sleepinterval"] = DEFAULT_SLEEP_INTERVAL
    
    if not desiredstate.get("enabled", False):
      print ("System is not Armed. Doing NOOP")
      redundant_water_off(desiredstate,thingname)
      return
        
    if (secondsfrommidnight < starttimefrommidnight):
      print ("Its too early for irrigation")
      redundant_water_off(desiredstate,thingname)
      deltaforstart = starttimefrommidnight - secondsfrommidnight
      if deltaforstart < desiredstate["sleepinterval"]:
        desiredstate["sleepinterval"] = deltaforstart
        push_state(DESIRED_KEY,{"sleepinterval" : deltaforstart},thingname)

      return
  
    if (secondsfrommidnight > endtimefrommidnight):
      print ("Its too late for irrigation")
      redundant_water_off(desiredstate,thingname)
      return

    lastwatering = reportedstate.get ("lastwatering",0)
    dosageinterval = desiredstate.get ("dosageinterval",10800)
    print ("Last Watering on {0}. Dosage Interval is {1}. Current Time is {2}".format(lastwatering,dosageinterval,nowepoch))
    
    lastwatering = reportedstate.get ("lastwatering",0)
    lastwateringupdate = metadata[REPORTED_KEY].get("lastwatering").get("timestamp",nowepochinlocaltime)

    #Less than 1st Jan 2017
    if lastwatering < 1483209000:
      #Something is wrong. use fuzzy logic
      #Update the last watering time to current time to avoid rewatering in the next wake up of The thing
      print ("Something is wrong. Last Watering time is {0}. Last Watering time updated on {1}. Fuzzing it up".format(lastwatering,lastwateringupdate))
      push_state(REPORTED_KEY,{"lastwatering" : lastwateringupdate},thingname)
      #Dont do any further processing. Next invocation will hopefully won't come here
      return

    if nowepoch >= lastwatering + dosageinterval:
      #Its time for action
      print ("We need to start the pump")
      desiredstate["waternow"] = True
      push_state(DESIRED_KEY,{"waternow" : True},thingname)
    else:
      deltatonextwatering = ( lastwatering + dosageinterval) - nowepoch
      desiredstate["sleepinterval"] = deltatonextwatering
      print ("Time to next watering is {0}".format(deltatonextwatering))
      push_state(DESIRED_KEY,{"sleepinterval" : deltatonextwatering},thingname)
      
      
def handler(event, context):
    
    #client = boto3.client('iot',region_name="us-west-2")
    #things = client.list_things()
    #print (len(things))
    for thingname in THINGNAMES:
      print ("Processing thing {0}".format(thingname))
      client = boto3.client('iot-data')
      response = client.get_thing_shadow(thingName= thingname)
      streamingBody = response["payload"]
      jsonState = json.loads(streamingBody.read())
      dologic (jsonState,thingname)
    
    # Your code goes here!
    #e = event.get('e')
    #pi = event.get('pi')
    #print ("Hello world {0}".format (e + pi))
    #return e + pi
