################################################################################
#                                                                              #
#  処理名      ：AMI世代管理                                                     #
#                                                                              #
#  処理内容    ：AMIの削除と世代管理を行う。                                      #
#                                                                              #
#  修正日        修正者       修正内容                                           #
# ============================================================================ #
#  2018/11/08    kpchnmn     新規作成                                          #
# ============================================================================ #
#  2019/04/22    kpchnmn     失敗時のみの通知を修正                             #
################################################################################
'''
AMI世代管理スクリプト

DailyAutoImageBackupタグが設定されたEC2インスタンスのAMI世代管理を行います。

#環境変数設定値#
SNS_TOPIC_ARN       結果通知用SNSトピックのARN
SEND_SNS_SUCCESS    処理成功時通知の有無 (True or Falseで指定)
DEBUG               デバッグログ出力の有無 (True or Falseで指定)

DailyAutoImageBackupタグが付与されているEC2インスタンスの[Generations]に
設定されている世代数を超えるAMIが存在する場合、古いものから順に削除します。
最新のAMI取得が成功していない場合は削除処理をスキップします。
処理完了後、設定されている通知先にSNSでメールを送信します。
SEND_SNS_SUCCESSをFalseに設定している場合は失敗時のみ通知を送信します。

AWS上で自動実行する場合はLambdaにFunctionとして登録し、Handlerにlambda_handlerを指定してください。
Lambdaから実行する場合はTIME_DIFF = 9を設定してください。
'''
import boto3
import json
import traceback
import dateutil
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

# SNSエラー通知
SEND_SNS = True

# SNS成功通知
if os.environ['SEND_SNS_SUCCESS'] == 'False':
    SEND_SNS_SUCCESS = False
else:
    SEND_SNS_SUCCESS = True

# AMI名Prefix
IMAGE_PREFIX = 'img_'

# SNS TOPIC
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

# SNS Subject
SNS_SUBJECT = 'バックアップ結果通知'

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

# バックアップ結果成否
BACKUP_SUCCESS = '成功'
BACKUP_FAILED = '失敗'

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

def updateNotifiedValue(tagValueList,notified):
    '''
    DailyAutoImageBackupタグの以下の値を更新します。
    ・Notified
    '''

    instanceIdList = [tagValueList.get(INSTANCEID)]
    tagValue = {}
    tagValue[NOTIFIED] = notified
    tagValue[LATEST_AMI_ID] = tagValueList.get(LATEST_AMI_ID)
    tagValue[REBOOT] = tagValueList.get(REBOOT)
    tagValue[GENERATIONS] = tagValueList.get(GENERATIONS)
    tagValue[TIME] = tagValueList.get(TIME)
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
    設定されているバックアップ情報に従ってAMIの世代管理を行います。
    '''

    print(logTime() + '================================')
    print(logTime() + 'AMI世代管理スクリプト処理 START')
    print(logTime() + '================================')

    status = STATUS_SUCCESS

    try:
        # メールタイトル用日付
        emailDate = nowJst().strftime('%Y-%m-%d')

        # AutoImageBackupタグでフィルタしてinstance情報取得
        describeResult = ec2Client.describe_instances(
            Filters=[{'Name':'tag-key','Values':[DAILY]}]
                                              ).get('Reservations')
        if DEBUG: pprint(describeResult)

        # インスタンスのタグからバックアップ設定情報を解析
        backupSettingLists = []
        for reservation in describeResult:
            backupSettingLists.append(parseEc2InstancesDailyBackupSetting(reservation.get('Instances')))

        # 取り出して削除
        for backupSettings in backupSettingLists:
            for backupSetting in backupSettings:
                print(logTime() + '-------------------------')
                print(logTime() + 'インスタンスID:' + backupSetting.get(INSTANCEID))
                if DEBUG: print(logTime() + 'バックアップ設定:' + str(backupSetting))

                try:
                    if not backupSetting.get('JsonCheckResult'):
                        print(logTime() + 'タグ設定値の形式が不正です。Json形式で記述してください。')
                        status = STATUS_WARNING
                        break

                    # LatestAmiId取り出し
                    latestAmiId = backupSetting.get(LATEST_AMI_ID)

                    # LatestAmiIdが設定されていない場合
                    if latestAmiId == '':
                        print(logTime() + 'LatestAmiId未設定のため処理をスキップします。')

                    # LatestAmiIdにCheckFailedが設定されている場合
                    elif latestAmiId != '' and latestAmiId == 'CheckFailed':
                        if backupSetting.get(NOTIFIED) == 'no':
                            # SNS通知
                            subject = '【' + BACKUP_FAILED + '】' + emailDate + ' バックアップ結果通知 : '\
                                     + backupSetting.get('Name') + ' (' + backupSetting.get(INSTANCEID) + ')'
                            msg = '自動バックアップ実施結果をお知らせします。\n\n'\
                                 + 'バックアップ実施結果 : ' + BACKUP_FAILED + '\n'\
                                 + '対象インスタンス ： ' + backupSetting.get(INSTANCEID) + '\n'\
                                 + 'インスタンスのタグ設定 (DailyAutoImageBackup) が不正のためバックアップに失敗しました。\n'\
                                 + 'タグの設定内容を確認してください。'

                            if SEND_SNS:
                                sendSns(subject, msg)
                                print(logTime() + '結果通知メールを [' + BACKUP_FAILED + ']で送信しました。')
                                # Notifiedをyesに更新
                                updateNotifiedValue(backupSetting,'yes')

                            print(logTime() + 'AMI作成に失敗しました。タグの設定値が不正です。')

                    # LatestAmiIdにAMI-IDが設定されている場合
                    elif latestAmiId != '':
                        print(logTime() + '最新のAMI-ID(LatestAmiId)：' + latestAmiId)
                        # AMI取得
                        images = ec2Client.describe_images(ImageIds = [latestAmiId]).get('Images')
                        if DEBUG: pprint(images)

                        for image in images:
                            amistate = image.get('State')
                            if amistate == 'available':
                                print(logTime() + latestAmiId + 'のAMIステータス：' + amistate)

                                # SrcInstanceIDとAutoImageBackupTypeでフィルターして関連するAMIを全て取得
                                allImages = ec2Client.describe_images(\
                                    Filters=[\
                                        {'Name':'tag-key','Values':['SrcInstanceId']},\
                                        {'Name':'tag-value','Values':[backupSetting.get(INSTANCEID)]},\
                                        {'Name':'tag-key','Values':['AutoImageBackupType']},\
                                        {'Name':'tag-value','Values':[DAILY]}\
                                            ]\
                                    ).get('Images')
                                if DEBUG: pprint(allImages)

                                # 保管世代数比較
                                gen = int(backupSetting.get(GENERATIONS))
                                amis = int(len(allImages))
                                delTargetNum = amis - gen
                                print(logTime() + '保管世代数：' + str(gen))
                                print(logTime() + '作成済AMI数：' + str(amis))

                                # 作成済AMI数が保管世代数を超えている場合
                                if amis > gen:
                                    # 削除用リスト作成
                                    delDict = {}
                                    delCounter = 1
                                    for delImage in allImages:
                                        delDict[delImage.get('ImageId')] = delImage.get('CreationDate')

                                    # 削除用リストを日付で昇順ソート
                                    for delAmi in sorted(delDict.items(), key=lambda x: x[1]):

                                        # 保管世代数を超えているAMIを古い順に削除
                                        if delCounter <= delTargetNum:
                                            print(logTime() + 'AMI-ID : ' + str(delAmi) + ' を登録解除します。')

                                            # AMI登録解除
                                            ec2Client.deregister_image(ImageId = delAmi[0])

                                            # EBS Snapshot削除
                                            for delImage2 in allImages:
                                                if delImage2.get('ImageId') == delAmi[0]:
                                                    for device in delImage2.get('BlockDeviceMappings'):
                                                        if 'Ebs' in device: # Ephemeral Disk対応 2018/02/20 add by hirahara
                                                            print(logTime() + 'Snapshot-ID : '\
                                                            + (device.get('Ebs')).get('SnapshotId') + ' を削除します。')
                                                            ec2Client.delete_snapshot(SnapshotId = (device.get('Ebs')).get('SnapshotId'))

                                        else:
                                            print(logTime() + 'AMI-ID : ' + str(delAmi) + ' を保管します。')

                                        delCounter = delCounter + 1

                                else:
                                    print(logTime() + '保管世代数以内のため処理をスキップします。')

                                # NotifiedがnoだったらSNSで成功通知してNotifiedをyesに更新
                                if backupSetting.get(NOTIFIED) == 'no':
                                    # SNS通知用CreationDate
                                    # YYYY-MM-DDTHH:MM:SS.000Z(UTC)をYYYY-MM-DD HH:MM:SS(ローカル)に変換
                                    parsedCreationDate = dateutil.parser.parse(image.get('CreationDate')).strftime('%Y-%m-%d %H:%M:%S')
                                    dtLocalCreationDate = datetime.strptime(parsedCreationDate,'%Y-%m-%d %H:%M:%S') + timedelta(hours=TIME_DIFF)
                                    # SNS通知
                                    subject = '【' + BACKUP_SUCCESS + '】' + emailDate + ' バックアップ結果通知 : '\
                                             + backupSetting.get('Name') + ' (' + backupSetting.get(INSTANCEID) + ')'
                                    msg = '自動バックアップ実施結果をお知らせします。\n\n'\
                                         + 'バックアップ実施結果 : ' + BACKUP_SUCCESS + '\n'\
                                         + 'バックアップ実施日時 : ' + str(dtLocalCreationDate) + '\n'\
                                         + '対象インスタンス ： ' + backupSetting.get(INSTANCEID) + '\n'\
                                         + 'AMI-ID ： ' + image.get('ImageId')

                                    if SEND_SNS:
                                        if SEND_SNS_SUCCESS:
                                            sendSns(subject, msg)
                                            print(logTime() + '結果通知メールを [' + BACKUP_SUCCESS + ']で送信しました。')
                                        updateNotifiedValue(backupSetting,'yes')

                            elif amistate == 'pending':
                                print(logTime() + latestAmiId + 'のAMIステータス：' + amistate)
                                print(logTime() + '最新AMIの作成が完了していないため処理をスキップします。')

                            elif amistate == 'failed':
                                print(logTime() + latestAmiId + 'のAMIステータス：' + amistate)
                                # NotifiedがnoだったらSNSで失敗通知してNotifiedをyesに更新
                                if backupSetting.get(NOTIFIED) == 'no':
                                    # SNS通知用CreationDate
                                    # YYYY-MM-DDTHH:MM:SS.000Z(UTC)をYYYY-MM-DD HH:MM:SS(ローカル)に変換
                                    parsedCreationDate = dateutil.parser.parse(image.get('CreationDate')).strftime('%Y-%m-%d %H:%M:%S')
                                    dtLocalCreationDate = datetime.strptime(parsedCreationDate,'%Y-%m-%d %H:%M:%S') + timedelta(hours=TIME_DIFF)
                                    # SNS通知
                                    subject = '【' + BACKUP_FAILED + '】' + emailDate + ' バックアップ結果通知 : '\
                                             + backupSetting.get('Name') + ' (' + backupSetting.get(INSTANCEID) + ')'
                                    msg = '自動バックアップ実施結果をお知らせします。\n\n'\
                                         + 'バックアップ実施結果 : ' + BACKUP_FAILED + '\n'\
                                         + 'バックアップ実施日時 : ' + str(dtLocalCreationDate) + '\n'\
                                         + '対象インスタンス ： ' + backupSetting.get(INSTANCEID) + '\n'\
                                         + 'AMI-ID ： ' + image.get('ImageId')
                                    if SEND_SNS:
                                        sendSns(subject, msg)
                                        print(logTime() + '結果通知メールを [' + BACKUP_FAILED + ']で送信しました。')
                                        updateNotifiedValue(backupSetting,'yes')

                except:
                    print(logTime() + 'インスタンスID:' + backupSetting.get(INSTANCEID) + 'のAMI世代管理処理で例外が発生しました。')
                    print(logTime() + traceback.format_exc())
                    status = STATUS_ERROR

        if status != STATUS_SUCCESS:
            raise AutoImageBackupException(status)

    except AutoImageBackupException:
        print(logTime() + 'AMI世代管理処理中に例外が発生しました。')
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