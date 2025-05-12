################################################################################
#                                                                              #
#  処理名      ：CloudWatchAlertAnalyzer                                       #
#                                                                              #
#  処理内容    ：CloudWatchAlermから送られるメッセージのカスタマイズ           #
#                                                                              #
#  修正日        修正者       修正内容                                         #
#  =========================================================================== #
#  2019/02/28    kpchnmn     新規作成                                         #
################################################################################
'''
SNSメッセージ日本語化スクリプト

主要な閾値監視通知のメッセージの日本語化を行います。

#環境変数設定値#
DEBUG               デバッグログ出力の有無 (True or Falseで指定)


AWS上で自動実行する場合はLambdaにFunctionとして登録し、Handlerにlambda_handlerを指定してください。
Lambdaから実行する場合はTIME_DIFF = 9を設定してください。
'''
import boto3
import traceback
import dateutil
import os
from datetime import datetime, timedelta
from pprint import pprint

# UTC -> JSTの変換に使用
TIME_DIFF = 9
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
DEBUG = os.environ['DEBUG']

# STATUS
STATUS_SUCCESS = 'SUCCESS'
STATUS_WARNING = 'WARNING'
STATUS_ERROR = 'ERROR'

# METRICNAME
METRICNAMECPU = 'CPUUtilization'
METRICNAMEsSTATUS = 'StatusCheckFailed_System'
METRICNAMEiSTATUS = 'StatusCheckFailed_Instance'
METRICNAMEwMEM = 'Memory'
METRICNAMEwVOL = 'LogicalDisk'

# EC2 resource
ec2 = boto3.resource('ec2')

def nowJst():
    '''
    現在時刻を取得します。
    TIME_DIFFにUTCとの時差を設定するとローカル時刻を返します。
    '''
    return datetime.now() + timedelta(hours=TIME_DIFF)

def logTime():
    '''
    ログ用の時刻を取得します。
    '''
    return nowJst().strftime('%Y/%m/%d %H:%M:%S') + " "

def msgAnalyze(message):
    '''
    SNSメッセージの内容を解析します。
    '''
    newMSG = message.replace('null','\"\"')
    if DEBUG:
        print(newMSG)
    msg = eval(newMSG)
    if DEBUG:
        pprint(msg)
        print(type(msg))
        print(msg['Trigger'])
    MetricName = msg['Trigger']['MetricName']

    if METRICNAMEwVOL in MetricName:
        MetricName = 'ストレージ空き容量'
        InstanceID = msg['Trigger']['Dimensions'][1]['value']
        Threshold =  msg['Trigger']['Threshold']
    else:
        if MetricName is METRICNAMECPU:
            MetricName = 'CPU使用率'
        if MetricName is METRICNAMEsSTATUS:
            MetricName = 'システムステータスチェック'
        if MetricName is METRICNAMEiSTATUS:
            MetricName = 'インスタンスステータスチェック'
        if METRICNAMEwMEM in MetricName:
            MetricName = 'メモリ使用率'

        InstanceID = msg['Trigger']['Dimensions'][0]['value']
        Threshold =  msg['Trigger']['Threshold']
    """
    if DEBUG:
        print(MetricName)
        print(InstanceID)
        print(Threshold)
    """
    instance = ec2.Instance(id=InstanceID)
    name_tag = [x['Value'] for x in instance.tags if x['Key'] == 'Name']
    name = name_tag[0] if len(name_tag) else ''
    """
    if DEBUG:
        print(name)
    """
    return {'MetricName':MetricName,'Instance':name,'Threshold':Threshold}

def makeMSG(contents):
    Title = contents['MetricName']

    subject = '【お知らせ】閾値監視結果 : ' + Title

    newmsg = '閾値監視結果をお知らせします。\n\n'\
                 + '【お知らせ内容】\n' + ' 対象インスタンスの ' + Title + ' が閾値を超えました。\n\n'\
                 + '対象インスタンス ： ' + contents['Instance'] + '\n'\
                 + '監視内容 : ' + Title + '\n'\
                 + '閾値：' + str(contents['Threshold']) + '\n'\


    return {'subject':subject,'newmsg':newmsg}

def sendSns(subject,msg):
    '''
    SNSでメッセージを送信します。
    '''

    snsClient = boto3.client('sns')

    snsRequest = {
        'TopicArn': SNS_TOPIC_ARN,
        'Subject': subject,
        'Message': msg
    }

    snsClient.publish(**snsRequest)


def lambda_handler(event,context):
    '''
    Lambdaから実行される関数です。
    '''
    if DEBUG:
        print(logTime()+'===================DEBUG START====================')
        pprint(event['Records'][0]['Sns'])

    SUBJECT =  event['Records'][0]['Sns']['Subject']

    if DEBUG:

        print(logTime() + SUBJECT)
        #print(type(SUBJECT))
        print('=================================')
    MESSAGE =  event['Records'][0]['Sns']['Message']

    if DEBUG:
        print(MESSAGE)
        print('=================================')
        print(type(MESSAGE))
    result = msgAnalyze(MESSAGE)
    if DEBUG:
        print(result)
    result = makeMSG(result)
    SUBJECT = result['subject']
    NEWMSG = result['newmsg']
    if DEBUG:
        print(SUBJECT)
        print(NEWMSG)

    sendSns(SUBJECT,NEWMSG)

    if DEBUG:
        print(logTime()+'===================DEBUG END====================')

    return 0