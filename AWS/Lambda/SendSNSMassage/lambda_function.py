################################################################################
#                                                                              #
#  処理名      ：SNSメッセージ送信                                               #
#                                                                              #
#  処理内容    ：SNSメッセージを送信する。                                        #
#                                                                              #
#  修正日        修正者       修正内容                                           #
#  =========================================================================== #
#  2019/02/12    kpchnmn     新規作成                                          #
################################################################################
'''
SNSメッセージ送信スクリプト

任意のSNSメッセージ送信を行います。

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
        print(logTime() + MESSAGE)
        print('=================================')
        #print(type(MESSAGE))
    sendSns(SUBJECT,MESSAGE)

    if DEBUG:
        print(logTime()+'===================DEBUG END====================')

    return 0