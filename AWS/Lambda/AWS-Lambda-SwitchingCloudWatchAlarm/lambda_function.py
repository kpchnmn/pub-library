import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('cloudwatch')

def disable_alarm(AlarmNames):
    for AlarmName in AlarmNames:
        logger.info("AlarmName: "+ AlarmName)
        response = client.disable_alarm_actions(
            AlarmNames=[AlarmName]
        )
    logger.info(response)

def enable_alarm(AlarmNames):
    for AlarmName in AlarmNames:
        logger.info("AlarmName: "+ AlarmName)
        response = client.enable_alarm_actions(
            AlarmNames=[AlarmName]
        )
    logger.info(response)

def lambda_handler(event, context):

    logger.info("event: "+ json.dumps(event))
    mode = event['mode']
    logger.info("mode: " + mode)

    AlarmNames = event["AlarmNames"]
    logger.info(AlarmNames)

    if mode == "disable":
        disable_alarm(AlarmNames)
    elif mode == "enable":
        enable_alarm(AlarmNames)
