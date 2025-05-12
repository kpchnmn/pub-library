################################################################################
#                                                                              #
#  処理名      ：AMI自動作成                                                   #
#                                                                              #
#  処理内容    ：AMIの作成を行う。                                             #
#                                                                              #
#  修正日        修正者       修正内容                                         #
#  =========================================================================== #
#  2018/11/08    kpchnmn     新規作成                                         #
################################################################################
'''
AMI自動作成スクリプト

DailyAutoImageBackupタグが設定されたEC2インスタンスのAMIを日次で自動作成します。

#環境変数設定値#
INTERVAL    実行間隔（分）
DEBUG       デバッグログ出力の有無 (True or Falseで指定)

対象EC2インスタンスのタグにKey:DailyAutoImageBackupを付与し、
以下のValueをJson形式で設定してください。

 ・Time : AMI作成実施時刻(HH:MM)
 ・Generations : 世代数(int)
 ・Reboot : AMI作成時リブート有無(yes:no)
 ・LatestAmiId : 最新AMI-ID (初期は空白[""]を設定)

 例) "LatestAmiId": "", "Reboot": "yes", "Generations": "1", "Time": "10:00"
 ※順序は関係ありません。

AWS上で自動実行する場合はLambdaにFunctionとして登録し、Handlerにlambda_handlerを指定してください。
Lambdaから実行する場合はTIME_DIFF = 9を設定してください。
INTERVALには実行間隔（分）を設定してください。

例）Lambdaから30分毎(毎時0分と30分)に自動実行する場合
 CloudWatchEventルールの設定
  スケジュール：Cron式 設定値：0-59/30 * * * ? *

 本スクリプトのINTERVAL設定(環境変数に設定)
  INTERVAL = 30

上記設定では毎時0分と30分にLambdaからスクリプトが起動され、
起動時の時刻を0分または30分に丸めたうえでAMI作成時刻の判定がされます。
 10:00:10に起動された場合、AMI作成判定時刻は10:00になります。
 10:30:05に起動された場合、AMI作成判定時刻は10:30になります。
 10:35:45に起動された場合、AMI作成判定時刻は10:30になります。

'''
import boto3
import json
import traceback
import re
import os
from datetime import datetime, timedelta
from pprint import pprint

# UTC -> JSTの変換に使用
TIME_DIFF = 9

# DEBUGモード
if os.environ['DEBUG'] == 'False':
    DEBUG = False
else:
    DEBUG = True

# 実行間隔（分）何分毎に実行するか
INTERVAL = int(os.environ['INTERVAL'])

# AMI名Prefix
IMAGE_PREFIX = 'img_'

# EC2バックアップ設定タグ
DAILY = 'DailyAutoImageBackup'
TIME = 'Time'
GENERATIONS = 'Generations'
REBOOT = 'Reboot'
LATEST_AMI_ID = 'LatestAmiId'
TERM = 'Term'
INSTANCEID = 'InstanceId'
NOTIFIED = 'Notified'

# AMIタグ
SRC_INSTANCE_ID = 'SrcInstanceId'
AUTO_IMAGE_BACKUP_TYPE = 'AutoImageBackupType'

# STATUS
STATUS_SUCCESS = 'SUCCESS'
STATUS_WARNING = 'WARNING'
STATUS_ERROR = 'ERROR'

# EC2 Client
ec2Client = boto3.client('ec2')

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

def roundingTime(time,interval):
    '''
    時刻丸め処理を行います。
    '''
    roundtime = interval * 60
    # 時刻丸め処理
    minSecond = ((time.minute * 60) + time.second)
    if DEBUG : print("現在時刻の分秒→秒：" + str(minSecond))
    HalfRoundTimePlus = minSecond + (roundtime / 2)
    if DEBUG : print("丸め時間の半分を追加：" + str(HalfRoundTimePlus))
    roundBlock = HalfRoundTimePlus / roundtime
    if DEBUG : print("丸め時間何個分存在するか（切り捨て）：" + str(roundBlock))
    roundTime = roundBlock * roundtime
    if DEBUG : print("丸め時間の個数×丸め時間：" + str(roundTime))
    adjustTime = roundTime - minSecond
    if DEBUG : print("調整時間：" + str(adjustTime))
    if DEBUG : print("時刻丸め処理実行後結果：" + str(time.replace(microsecond=0) + timedelta(seconds=adjustTime)))
    return time.replace(microsecond=0) + timedelta(seconds=adjustTime)

def floorTime(time,interval):
    '''
    時刻の丸め処理を行います。
    1時間をintervalに指定された値で区切って基準時刻とし、
    現在時刻から最も近い過去の基準時刻を返します。
    '''
    roundtime = interval * 60
    # 起動時刻用
    minSecond = ((time.minute * 60) + time.second)
    if DEBUG : print("現在時刻の分秒→秒：" + str(minSecond))
    roundBlock = minSecond / roundtime
    if DEBUG : print("丸め時間何個分存在するか（切り捨て）：" + str(roundBlock))
    roundTime = roundBlock * roundtime
    if DEBUG : print("丸め時間の個数×丸め時間：" + str(roundTime))
    adjustTime = roundTime - minSecond
    if DEBUG : print("調整時間：" + str(adjustTime))
    if DEBUG : print("時刻丸め処理実行後結果：" + str(time.replace(microsecond=0) + timedelta(seconds=adjustTime)))
    return time.replace(microsecond=0) + timedelta(seconds=adjustTime)

def ceilingTime(time,interval):
    '''
    時刻丸め処理を行います。
    1時間をintervalに指定された値で区切って基準時刻とし、
    現在時刻から最も近い未来の基準時刻を返します。
    '''
    roundtime = interval * 60
    # 停止時刻用
    minSecond = ((time.minute * 60) + time.second)
    if DEBUG : print("現在時刻の分秒→秒：" + str(minSecond))
    roundTimePlus = minSecond + roundtime - 1
    if DEBUG : print("丸め時間を追加：" + str(roundTimePlus))
    roundBlock = roundTimePlus / roundtime
    if DEBUG : print("丸め時間何個分存在するか（切り捨て）：" + str(roundBlock))
    roundTime = roundBlock * roundtime
    if DEBUG : print("丸め時間の個数×丸め時間：" + str(roundTime))
    adjustTime = roundTime - minSecond
    if DEBUG : print("調整時間：" + str(adjustTime))
    if DEBUG : print("時刻丸め処理実行後結果：" + str(time.replace(microsecond=0) + timedelta(seconds=adjustTime)))
    return time.replace(microsecond=0) + timedelta(seconds=adjustTime)

def checkAutoImageBackupSetting(setting):
    '''
    DailyAutoImageBackupタグの設定値をチェックし、結果をdict{}で返します。

     CheckResult : チェック結果をTrue or Falseで格納
     チェックエラー発生時には項目をキーにエラー内容を格納して返します。
    '''

    result = {'CheckResult':True}

    if not setting.get('JsonCheckResult'):
        if DEBUG: print(TIME + 'タグ設定値の形式が不正です。Json形式で記述してください。')
        result['CheckResult'] = False
        result['JsonCheckResult'] = 'タグ設定値の形式が不正です。Json形式で記述してください。'

    if TIME not in setting:
        if DEBUG: print(TIME + 'キーが設定されていません')
        result['CheckResult'] = False
        result[TIME] = ('キーが設定されていません')
    else:
        if not setting.get(TIME):
            if DEBUG:print(TIME + 'の値が設定されていません')
            result['CheckResult'] = False
            result[TIME] = '値が設定されていません。'
        # 時刻形式チェック
        else:
            try:
                datetime.strptime(setting.get(TIME),'%H:%M')
            except:
                result['CheckResult'] = False
                result[TIME] = '設定値エラー。 時刻形式(HH:MM)を設定してください。 '

    if GENERATIONS not in setting:
        if DEBUG:print(GENERATIONS + 'キーが設定されていません')
        result['CheckResult'] = False
        result[GENERATIONS] = 'キーが設定されていません'
    else:
        if not setting.get(GENERATIONS):
            if DEBUG: print(GENERATIONS + 'の値が設定されていません')
            result['CheckResult'] = False
            result[GENERATIONS] = '値が設定されていません。'
        else:
            # 数字チェック
            if not setting.get(GENERATIONS).isdigit():
                result['CheckResult'] = False
                result[GENERATIONS] = '設定値エラー。数値を設定してください。'

    if REBOOT not in setting:
        if DEBUG: print(REBOOT + 'キーが設定されていません')
        result['CheckResult'] = False
        result[REBOOT] = 'キーが設定されていません'
    else:
        if not setting.get(REBOOT):
            if DEBUG: print(REBOOT + 'の値が設定されていません')
            result['CheckResult'] = False
            result[REBOOT] = '値が設定されていません。'
        else:
            if not (re.compile(setting.get(REBOOT), re.IGNORECASE).match('no') or re.compile(setting.get(REBOOT), re.IGNORECASE).match('yes')):
                result['CheckResult'] = False
                result[REBOOT] = '設定値エラー. 次の値を設定してください。yes[yes,Yes,YES] or no[no,No,NO]'

    if LATEST_AMI_ID not in setting:
        if DEBUG: print(LATEST_AMI_ID + 'キーが設定されていません')
        result['CheckResult'] = False
        result[LATEST_AMI_ID] = 'キーが設定されていません'

    return result

def parseEc2InstancesDailyBackupSetting(instances):
    '''
    DailyAutoImageBackupタグが設定されているインスタンスのタグ値を解析し、結果をlist[dict{}]で返します。
    '''

    BackupSettingList = []
    for instance in instances:
        backupSetting = {}
        name = ''
        jsonCheckResult = True
        print(logTime() + '--------------------------------------------------')
        for tags in instance.get('Tags'):
            if tags.get('Key') == 'Name':
                name = tags.get('Value')
            if tags.get('Key') == DAILY:
                # JSON解析、バックアップセッティングディクショナリー作成
                try:
                    backupSetting = json.loads('{' + tags.get('Value') + '}')
                    print(logTime() + 'インスタンスID：' + instance.get('InstanceId') + 'のタグ設定値JSON解析完了')
                    if DEBUG: print(json.dumps(backupSetting, sort_keys = True, indent = 4))
                except:
                    print(logTime() + 'インスタンスID：' + instance.get('InstanceId') + 'のタグ設定値JSON解析失敗')
                    pprint(instance.get('Tags'))
                    jsonCheckResult = False

                backupSetting[TERM] = DAILY

        backupSetting['JsonCheckResult'] = jsonCheckResult
        backupSetting[INSTANCEID] = instance.get(INSTANCEID)
        backupSetting['Name'] = name
        if DEBUG: print(backupSetting)
        # バックアップセッティングディクショナリーをリストに格納
        BackupSettingList.append(backupSetting)

    return BackupSettingList

def updateLatestAmiIdValue(tagValueList,amiId):
    '''
    DailyAutoImageBackupタグの以下の値を更新します。
    ・LatestAmiId
    '''
    instanceIdList = [tagValueList.get(INSTANCEID)]
    tagValue = {}
    tagValue[LATEST_AMI_ID] = amiId
    tagValue[REBOOT] = tagValueList.get(REBOOT)
    tagValue[GENERATIONS] = tagValueList.get(GENERATIONS)
    tagValue[TIME] = tagValueList.get(TIME)
    tagValue[NOTIFIED] = 'no'
    jsonTagValue = json.dumps(tagValue).replace('{','').replace('}','')
    ec2Client.create_tags(
                         Resources = instanceIdList,
                         Tags = [
                            {
                                'Key' : tagValueList.get(TERM),
                                'Value' : str(jsonTagValue)
                            }
                        ]
                    )

def updateAmiTags(amiId,amiName,instanceId):
    '''
    amiIdに指定されたAMIに、以下のタグを設定します。
    ・Name
    ・SrcInstanceId
    ・AutoImageBackupType
    '''
    amiIdList = [amiId]
    ec2Client.create_tags(
                        Resources = amiIdList,
                        Tags = [
                            {
                                'Key' : 'Name',
                                'Value' : amiName
                             },
                            {
                                'Key' : SRC_INSTANCE_ID,
                                'Value' : instanceId
                             },
                            {
                                'Key' : AUTO_IMAGE_BACKUP_TYPE,
                                'Value' : DAILY
                             }
                        ]
    )

class AutoImageBackupException(Exception):
    '''
    AutoImageBackup例外クラス
    '''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def lambda_handler(event,context):
    '''
    Lambdaから実行される関数です。
    DailyAutoImageBackupタグが設定されているEC2インスタンスの情報を取得し、
    設定されているバックアップ情報に従ってAMIを作成します。
    '''
    print(logTime() + '================================')
    print(logTime() + 'AMI自動作成スクリプト処理 START')
    print(logTime() + '================================')

    status = STATUS_SUCCESS

    try:
        # AutoImageBackupタグでフィルタしてinstance情報取得
        describeResult = ec2Client.describe_instances(
            Filters=[{'Name':'tag-key','Values':[DAILY]}]
                                              ).get('Reservations')

        if DEBUG: pprint(describeResult)

        if len(describeResult) > 0:
            # インスタンスのタグからバックアップ設定情報を解析
            backupSettingLists = []
            for reservation in describeResult:
                backupSettingLists.append(parseEc2InstancesDailyBackupSetting(reservation.get('Instances')))
            if DEBUG: pprint(backupSettingLists)

            # 実施判定用時刻
            roundedCurrentTime = (floorTime(nowJst(),INTERVAL)).strftime('%H:%M')
            print(logTime() + '-------------------------')
            print(logTime() + '実施判定用基準時刻：' + str(roundedCurrentTime))

            # 解析したバックアップ設定をチェックしてバックアップ
            for backupSettings in backupSettingLists:
                for backupSetting in backupSettings:
                    print(logTime() + '-------------------------')
                    print(logTime() + 'インスタンスID:' + backupSetting.get(INSTANCEID))
                    if DEBUG: print(logTime() + 'バックアップ設定:' + str(backupSetting))
                    # 設定値チェック
                    checkResults = checkAutoImageBackupSetting(backupSetting)
                    if DEBUG: print(logTime() + 'バックアップ設定チェック結果：' + str(checkResults))

                    if checkResults.get('CheckResult'):
                        # 日次
                        if backupSetting.get(TERM) == DAILY:
                            # 実施時刻判定
                            print(logTime() + '実施判定用基準時刻：' + str(roundedCurrentTime) + '  実施時刻設定値：' + backupSetting.get(TIME))
                            if backupSetting.get(TIME) == roundedCurrentTime:
                                print(logTime() + '実施判定用基準時刻と実施時刻設定値が一致したためAMI作成処理を実施します。')
                                noReboot = False
                                # AMI名
                                amiName = IMAGE_PREFIX + backupSetting.get('Name') + '(' + backupSetting.get(INSTANCEID)\
                                         + ')_' + nowJst().strftime('%Y%m%d-%H%M%S')
                                if DEBUG: print(amiName)
                                if backupSetting.get(REBOOT) == 'yes':
                                    noReboot = False
                                elif backupSetting.get(REBOOT) == 'no':
                                    noReboot = True

                                # AMI作成
                                descriptionStrings = 'Created by Daily Auto Image Backup Script'
                                try:
                                    amiId = ec2Client.create_image(InstanceId = backupSetting.get(INSTANCEID),\
                                                                   NoReboot = noReboot,\
                                                                   Name = amiName,\
                                                                   Description = descriptionStrings).get('ImageId')

                                    print(logTime() + 'AMI作成処理実施  AMI-ID：' + amiId)

                                    # インスタンスのLatestAmiIDを書きかえる
                                    updateLatestAmiIdValue(backupSetting, amiId)

                                    # AMIのタグを編集する
                                    updateAmiTags(amiId,amiName,backupSetting.get(INSTANCEID))
                                except:
                                    # 例外発生時はログを出力して処理を続行
                                    print(logTime() + 'インスタンスID : ' + backupSetting.get(INSTANCEID) + ' のAMI作成処理で例外が発生しました。')
                                    print(logTime() + traceback.format_exc())
                                    status = STATUS_ERROR

                            else:
                                print(logTime() + '実施判定用基準時刻と実施時刻設定値が一致しないためAMI作成処理をスキップします。')
                    else:

                        print(logTime() + 'インスタンスID:[' + backupSetting.get(INSTANCEID)\
                                        + '] Name:[' + backupSetting.get('Name') + ']のバックアップ設定が不正です。')

                        for item in checkResults:
                            print(logTime() + '  ' + item + ' : ' + str(checkResults.get(item)))

                        # LatestAmiIdにCheckFailed設定
                        updateLatestAmiIdValue(backupSetting, 'CheckFailed')
                        status = STATUS_WARNING

        else:
            print(logTime() + 'バックアップ実施対象インスタンスなし')

        if status != STATUS_SUCCESS:
            raise AutoImageBackupException(status)

    except AutoImageBackupException:
        print(logTime() + 'AMI作成処理中に例外が発生しました。')
        print(logTime() + traceback.format_exc())
        raise

    except:
        print(logTime() + '例外が発生しました。処理を終了します。')
        print(logTime() + traceback.format_exc())
        status = STATUS_ERROR
        raise

    finally:

        print(logTime() + '=====================================')
        print(logTime() + 'AMI自動作成スクリプト処理 END:' + status)
        print(logTime() + '=====================================')

    return 0