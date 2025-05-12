import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app

def sort_ec2(ec2):

    var = []
    if len(ec2['Tags']) >= 0 :
        for ec2_tag in ec2['Tags']:
            if ec2_tag['Key'] == 'Name':
                var.append(ec2_tag['Value'])
    else:
        var.append('')
    var.append(ec2['InstanceId'])
    var.append(ec2['InstanceType'])
    try:
        var.append(ec2['PublicIpAddress'])
    except:
        var.append('')
    try:
        var.append(ec2['PublicDnsName'])
    except:
        var.append('')
    try:
        var.append(ec2['PrivateIpAddress'])
    except:
        var.append('')
    try:
        var.append(ec2['PrivateDnsName'])
    except:
        var.append('')
    try:
        var.append(ec2['ImageId'])
    except:
        var.append('')
    try:
        var.append(ec2['KeyName'])
    except:
        var.append('')
    try:
        var.append(ec2['Placement']['AvailabilityZone'])
    except:
        var.append('')
    try:
        var.append(ec2['IamInstanceProfile']['Arn'])
    except:
        var.append('')
    try:
        var.append(ec2['VpcId'])
    except:
        var.append('')
    try:
        var.append(ec2['SubnetId'])
    except:
        var.append('')
    securitygroups = []
    for sg in ec2['SecurityGroups']:
        try:
            securitygroups.append(sg['GroupId'])
        except:
            securitygroups.append('')
    var.append(securitygroups)
    blockdevices = []
    for ebs in ec2['BlockDeviceMappings']:
        try:
            blockdevices.append(ebs['Ebs']['VolumeId'])
        except:
            blockdevices.append('')
    var.append(blockdevices)
    networkinterfaces = []
    for eni in ec2['NetworkInterfaces']:
        try:
            networkinterfaces.append(eni['NetworkInterfaceId'])
        except:
            networkinterfaces.append('')
    var.append(networkinterfaces)

    return var

def describe_ec2s(wb,ws):

    response = app.ec2.describe_instances()

    for idx,cell in enumerate(app.ec2_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font

    try:
        for idx, ec2 in enumerate(response['Reservations'],2):
            if idx == 2:
                count = idx
            else:
                count += 1
            res = sort_ec2(ec2['Instances'][0])

            if len(res[13]) > len(res[14]):
                if len(res[13]) > len(res[15]):
                    lres = len(res[13]) #SecurityGroup
                else:
                    lres = len(res[15]) #ENI
            else:
                if len(res[14]) > len(res[15]):
                    lres = len(res[14]) #EBS
                else:
                    lres = len(res[15]) #ENI
            if lres > 1: #SecurityGroup
                for l in range(lres):
                    for i , cell in enumerate(res,1):
                        if l > 0:
                            if i > 13: #SecurityGroup
                                try:
                                    ws.cell(row=count+l,column=i,value=cell[l]).font = app.font
                                except:
                                    pass
                        else:
                            if i > 13: #SecurityGroup
                                ws.cell(row=count,column=i,value=cell[l]).font = app.font
                            else:
                                ws.cell(row=count,column=i,value=str(cell)).font = app.font
                count += lres - 1
            else:
                for i , cell in enumerate(res,1):
                    if i > 13: #SecurityGroup
                        ws.cell(row=count,column=i,value=cell[0]).font = app.font
                    else:
                        ws.cell(row=count,column=i,value=str(cell)).font = app.font

    except:
        pass


def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.ec2_title]
    except:
        ws = wb.create_sheet(title=app.ec2_title)
    describe_ec2s(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'ec2.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)