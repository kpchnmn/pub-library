################################################################################
#                                                                              #
#  処理名      ：Sorryサーバフェイルオーバーリストア                           #
#                                                                              #
#  処理内容    ：ALBのヘルスチェック成功をトリガーにリスナーにルールを削除する #
#                                                                              #
#  修正日        修正者       修正内容                                         #
#  =========================================================================== #
#  2018/11/19    kpchnmn     新規作成                                         #
################################################################################
'''
ヘルスチェック正常をトリガーにALBにルールを削除するスクリプト
ALBAutoRuleRestore

#環境変数設定値#
DEBUG          デバッグログ出力の有無 (True or Falseで指定)
LISTENERARN    ALBのリスナーのARNを指定
TARGETGROUPARN ALBのターゲットグループのARNを指定

AWS上で自動実行する場合はLambdaにFunctionとして登録し、Handlerにlambda_handlerを指定してください。
Lambdaから実行する場合はTIME_DIFF = 9を設定してください。

'''
import boto3
import json
import os
from datetime import datetime, timedelta

# UTC -> JSTの変換に使用
TIME_DIFF = 9

# DEBUGモード
if os.environ['DEBUG'] == 'False':
    DEBUG = False
else:
    DEBUG = True

#ALBのリスナーARN
LNARN = os.environ['LISTENERARN']
#TargetGroupのARN
TGARN = os.environ['TARGETGROUPARN']

#ALBクライアント
elbv2 = boto3.client('elbv2')

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

def alb_delete_rule(RARN):
    '''
    指定したRuleArnのルールを削除します
    '''
    response=True
    try:
        elbv2.delete_rule(RuleArn=RARN)
        print(logTime() + 'ルールを削除しました。')
    except:
        response=False
    return response

def alb_describe_helthcheck(TGARN):
    '''
    指定したTargetGroupArnのヘルスチェックのステータスを返します。
    '''
    response = elbv2.describe_target_health(TargetGroupArn=TGARN)
    thd = response.get('TargetHealthDescriptions')[0]
    targethelth = thd.get('TargetHealth')
    status = targethelth.get('State')
    print(logTime() + "ヘルスチェックのステータス："+ status)
    return status

def describe_status(status,reason):
    '''
    処理が正常か、非正常の場合理由を返します
    '''
    response = ''
    if status:
        response = '処理は正常に実行されました'
    else:
        response = reason + 'のため処理は正常に実行されませんでした'
    print(logTime() + "------end-----------")
    return response

def lambda_handler(event, context):

    '''
    Main関数：処理結果を返します
    '''

    print(logTime() + "------start----------")
    status = True
    reason = ''
    try:
        #ターゲットグループのヘルスチェックの結果を取得
        helthstatus = alb_describe_helthcheck(TGARN)
    except:
        print('設定値エラー。ターゲットグループのARNが正しく設定されていません。')
        status =False
    if status:
        if helthstatus == 'healthy':
            try:
                #リスナーのルールを表示
                response = elbv2.describe_rules(ListenerArn=LNARN)
                rules = response.get('Rules')
            except:
                status=False
                print('設定値エラー。リスナーのARNが正しく設定されていません。')
            if status:
                print(logTime() + '読み込んだルールの数:'+ str(len(rules)))
                #ルールが既に設定されている場合は削除する
                if len(rules)==2:
                    RuleArn = rules[0].get('RuleArn')
                    print(logTime() + 'ルールの削除を実施します。')
                    status = alb_delete_rule(RuleArn)
                if status:
                    try:
                        albrulecreate = alb_create_rule(LNARN,html)
                        print(logTime() + 'ルールは正常に削除されました。')
                        return describe_status(status,reason)
                    except:
                        print(logTime() + 'ルールは１つのため実施しませんでした' )
                else:
                    print('削除実行エラー。ルールの削除に失敗しました。')

            else:
                reason='設定値エラー'
                return describe_status(status,reason)

        else:
            status = False
            reason = 'ヘルスチェック非正常'
            return describe_status(status,reason)
    else:
        reason = '設定値エラー'
        return describe_status(status,reason)

    return describe_status(status,reason)
