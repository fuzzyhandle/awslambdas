from __future__ import print_function
import tweepy
import json
import pprint


# Using twitter account hd_irrigation01
# Using keys from app https://apps.twitter.com/app/13837356/keys
# Email for account hrishikesh.date+hd_irrigation01@gmail.com

with open('./twitterconfig.json', 'r') as file:
    config = json.loads(file.read())
    
    CONSUMER_KEY = config['consumer-key']
    CONSUMER_SECRET = config['consumer-secret']
    ACCESS_TOKEN = config['access-token']
    ACCESS_TOKEN_SECRET = config['access-token-secret']


def handler(event, context):
    pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(event)
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    
    stateobj = None
    statereportedobj = None
    statedesiredobj = None
    
    metadataobj = None
    
    if event.has_key("state"):
      stateobj = event["state"]
      statedesiredobj = stateobj.get("desired")
      statereportedobj = stateobj.get("reported")
      
    if event.has_key("metadata"):
      metadataobj = event["metadata"]
    
    if statereportedobj:
      #Check if this is a heatbeat update
      if metadataobj.get("reported",{}).has_key("heartbeat"):
        heartbeat = statereportedobj["heartbeat"]
        api.update_status(u'Received Heartbeat with value {0}'.format(heartbeat))

      if metadataobj.get("reported",{}).has_key("lastwatering"):
        lastwatering = statereportedobj["lastwatering"]
        api.update_status(u'Irrigation cycle ran at {0}'.format(lastwatering))
      
    if statedesiredobj:
      if statedesiredobj.has_key("waternow"):
        waternow = statedesiredobj["waternow"]
        if waternow:
          api.update_status(u'Its time to run the irrigation cycle')