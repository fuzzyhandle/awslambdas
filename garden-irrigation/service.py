# -*- coding: utf-8 -*-
import boto3
import json
import time
import datetime 



TIMEZONEOFFSET = 5 * 3600 + 30 * 60
THINGNAME ='mama-garden-irrigation'

def dologic(stateobj):

    nowtiomeobj = datetime.datetime.now() +  datetime.timedelta(seconds =TIMEZONEOFFSET )
    nowepoch = time.mktime(nowtiomeobj.timetuple())

    secondsfrommidnight = nowepoch % 86400
    
    desiredstate =  stateobj['state']['desired']
    reportedstate =  stateobj['state']['reported']
    
    starttimefrommidnight = desiredstate.get ("dailystarttime",0)
    endtimefrommidnight = desiredstate.get ("dailyendtime",0)
    
    if not desiredstate.get("enabled", False):
      print ("System is not Armed. Doing NOOP")
      return
        
    if (secondsfrommidnight < starttimefrommidnight):
      print ("Its too early for irrigation")
      return
  
    if (secondsfrommidnight > endtimefrommidnight):
      print ("Its too late for irrigation")
      return

          
    
    lastwatering = reportedstate.get ("lastwatering",0)
    dosageinterval = desiredstate.get ("dosageinterval",10800)
    
    if nowepoch > lastwatering + dosageinterval:
      #Its time for action
      desiredstate["waternow"] = True
      
      print ("We need to start the pump")
      
      mypayload = json.dumps(
          {"state":{"desired":desiredstate}}
      
      )
      client = boto3.client('iot-data')
      print (stateobj)
      response = client.update_thing_shadow(thingName= THINGNAME,payload=mypayload)

    

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