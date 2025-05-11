import boto3
import os
import pprint

DEBUG = os.environ['DEBUG']
sDEBUG = '========================='

CVEid = os.environ['CLIENT_VPNENDPOINT_ID']
sbnetID = os.environ['SUBNET_ID']

ec2client = boto3.client('ec2')

def associate_client_vpn_target_network(id):
    '''
    ClientVPNの関連付けを作成します。
    '''
    response = ec2client.associate_client_vpn_target_network(ClientVpnEndpointId=id,SubnetId=sbnetID,ClientToken='200',DryRun=False)
    if DEBUG:
        pprint.pprint(response)
    print('ClientVPNの関連付けを作成しました。')


def disassociate_client_vpn_target_network(id,result):
    '''
    ClientVPNの関連付けを削除します。
    '''
    response = ec2client.disassociate_client_vpn_target_network(ClientVpnEndpointId=id,AssociationId=result)
    if DEBUG:
        pprint.pprint(response)
    print('ClientVPNの関連付けを解除しました。')


def lambda_handler(event, context):
    '''
    メイン関数
    '''
    process = event['process']
    if DEBUG:
        print(sDEBUG + 'DEBUG START' + sDEBUG)
    response = ec2client.describe_client_vpn_target_networks(ClientVpnEndpointId=CVEid)

    if response['ClientVpnTargetNetworks'] == []:
        if process == 'create':
            if DEBUG:
                print('Process:Create Started')
            associate_client_vpn_target_network(CVEid)

        elif process == 'delete':
            print('関連付けがされていないか既に削除済です。')

        else:
            print('定数が正しい形式で指定されていません。')

    else:
        result = response['ClientVpnTargetNetworks'][0]['AssociationId']
        if DEBUG:
            pprint.pprint(response)
            print('AssociationId = ' + result)

        if process == 'create':
            if DEBUG:
                print('関連付けが削除中か既に作成済です。')

        elif process == 'delete':
            if DEBUG:
                print('Process: Delete Started')
            disassociate_client_vpn_target_network(CVEid,result)

        else:
            print('定数が正しい形式で指定されていません。')

    if DEBUG:
        print(sDEBUG + 'DEBUG END' + sDEBUG)

    return 0