# -*- coding: utf-8 -*-
################################################################################
#                                                                              #
#  処理名      ：スナップショットタグ作成                                         #
#                                                                              #
#  処理内容    ：CostCenterタグのついていないスナップショットにタグを設定します。    #
#                                                                              #
#  修正日        修正者       修正内容 　                                        #
#  =========================================================================== #
#  2018/09/13    kpchnmn      新規作成                                         #
################################################################################
u'''
スナップショットタグ作成スクリプト

CostCenterタグが設定されていないスナップショットにタグを作成します。

#環境変数設定値#
OWNERID     所有者(アカウントID)
DEBUG       デバッグログ出力の有無 (True or Falseで指定)

'''
import json
import boto3
import os
import traceback
import re
import time
from datetime import datetime, timedelta, date
from pprint import pprint

# UTC -> JSTの変換に使用
TIME_DIFF = 9

# DEBUGモード
if os.environ['DEBUG'] == 'False':
    DEBUG = False
else:
    DEBUG = True

OwnerId = os.environ['OWNERID']


SNAPSHOTID = 'snapshotid'
COSTCENTER = 'CostCenter'
NoneVolume = 'vol-ffffffff'

# STATUS
STATUS_SUCCESS = 'SUCCESS'
STATUS_WARNING = 'WARNING'
STATUS_ERROR = 'ERROR'

# EC2 Client
ec2Client = boto3.client('ec2')

def nowJst():
    u'''
    現在時刻を取得します。
    TIME_DIFFにUTCとの時差を設定するとローカル時刻を返します。
    '''
    return datetime.now() + timedelta(hours=TIME_DIFF)

def logTime():
    u'''
    ログ用の時刻を取得します。
    '''
    return nowJst().strftime('%Y/%m/%d %H:%M:%S') + " "


def check_volumeList(snapshotList):
    u'''
    volumeが存在しないスナップショットをリストから排除します
    '''
    newSnapshotList =[]
    for snapshot in snapshotList:
        volumeid = snapshot.get('VolumeId')
        if volumeid != NoneVolume:
            newSnapshotList.append(snapshot)
    return newSnapshotList

#
def check_volumeIdList(snapshotList):
    u'''
    volumeが存在するスナップショットのIDとCostCenterを取得します
    '''
    settingList = []
    for snapshot in snapshotList:
        volumeid = snapshot.get('VolumeId')
        try:
            Volumes = ec2Client.describe_volumes(Filters=[],VolumeIds = [volumeid]).get('Volumes')
            if DEBUG: print u"存在する：voluemeid＝"+ volumeid
            for volume in Volumes:
                volumeTags = volume.get('Tags')
                for tag in volumeTags :
                    #CostCenterタグが設定されているvolumeの値を格納
                    if tag.get('Key') == COSTCENTER:
                        setting = {}
                        setting[COSTCENTER] = tag.get('Value')
                        setting[SNAPSHOTID] = snapshot.get('SnapshotId')
                        settingList.append(setting)
        except:
            if DEBUG: print u"存在しない：voluemeid＝"+ volumeid
            pass
    return settingList

def updateSnapshotTags(SnapshotId,costcenter):
    u'''
    指定されたIDのスナップショットにタグを設定します。
    ・Name
    ・CostCenter
    '''
    SnapshotIdList = [SnapshotId]
    ec2Client.create_tags(
        Resources = SnapshotIdList,
        Tags = [
            {
                'Key' : COSTCENTER,
                'Value' : costcenter
            }
            ]
    )

class SmapshotTagCreateException(Exception):
    u'''
    SmapshotTagCreate例外クラス
    '''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def lambda_handler(event, context):
    u'''
    Lambdaから実行される関数です。
    CostCenterタグが設定されているEBSボリュームの情報を取得し、
    設定されてないスナップショットにタグを作成します。
    '''

    print logTime() + u'================================'
    print logTime() + u'スナップショットタグ作成スクリプト処理 START'
    print logTime() + u'================================'

    status = STATUS_SUCCESS
    try:
        #所有するスナップショットリストをすべて取得する
        describeresult = ec2Client.describe_snapshots(
            Filters= [],
                    OwnerIds = [OwnerId]
                    ).get('Snapshots')
        #if DEBUG: pprint(describeresult)

        if len(describeresult) > 0:


            #volumeが存在しないスナップショットをリストから排除
            snapshotList = check_volumeList(describeresult)
            #if DEBUG: pprint(snapshotList)

            #volumeが存在するスナップショットのIDとCostCenterを取得
            settingList= check_volumeIdList(snapshotList)
            if DEBUG: print logTime() + u'================================'
            if DEBUG: pprint(settingList)

            #取得したIDのスナップショットにCostCenterタグを作製
            for setting in settingList:
                updateSnapshotTags(setting.get(SNAPSHOTID),setting.get(COSTCENTER))

        else:
            print logTime() + u'スナップショットタグ作成実施対象インスタンスなし'

        if status != STATUS_SUCCESS:
            raise SmapshotTagCreateException(status)

    except SmapshotTagCreateException:
        print logTime() + u'スナップショットタグ作成処理中に例外が発生しました。'
        print logTime() + traceback.format_exc()
        raise

    except:
        print logTime() + u'例外が発生しました。処理を終了します。'
        print logTime() + traceback.format_exc()
        status = STATUS_ERROR
        raise

    finally:

        print logTime() + u'====================================='
        print logTime() + u'スナップショットタグ作成作成スクリプト処理 END:' + status
        print logTime() + u'====================================='

    return 0

