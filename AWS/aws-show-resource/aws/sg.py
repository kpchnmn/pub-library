import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app

def sort_sg(sg):
    var = []
    try:
        for idx, sg_tag in enumerate(sg['Tags']):
            if idx > 0:
                pass
            else:
                if sg_tag['Key'] == 'Name':
                    var.append(sg_tag['Value'])
                else:
                    var.append('')
    except:
        var.append('')
    var.append(sg['GroupId'])
    var.append(sg['GroupName'])
    var.append(sg['Description'])
    var.append(sg['VpcId'])
    InProtocols = []
    InPortRanges = []
    InIpRanges = []
    InDescriptions = []
    for IpPermission in sg['IpPermissions']:
        try:
            if IpPermission['IpProtocol'] == '-1':
                InProtocols.append('すべて')
            else:
                InProtocols.append(IpPermission['IpProtocol'])
        except:
            InProtocols.append('')
        lres = len(IpPermission['IpRanges']) + len(IpPermission['UserIdGroupPairs'])
        if lres == 0:
            lres = 1
        count = 0
        for l in range(lres):
            try:
                if IpPermission['FromPort'] == IpPermission['ToPort']:
                    InPortRanges.append(IpPermission['FromPort'])
                else:
                    InPortRanges.append(str(IpPermission['FromPort']) + '-' + str(IpPermission['ToPort']))
            except:
                InPortRanges.append('')
            if l < len(IpPermission['IpRanges']):
                count += 1
                try:
                    InIpRanges.append(IpPermission['IpRanges'][l]['CidrIp'])
                    try:
                        InDescriptions.append(IpPermission['IpRanges'][l]['Description'])
                    except:
                        InDescriptions.append('')
                except:
                    InIpRanges.append('')
            else:
                l = l - count
                if l < 0:
                    l = 0
                try:
                    InIpRanges.append(IpPermission['UserIdGroupPairs'][l]['GroupId'])
                    try:
                        InDescriptions.append(IpPermission['UserIdGroupPairs'][l]['Description'])
                    except:
                        InDescriptions.append('')
                except:
                    InIpRanges.append('')

    var.append(InProtocols)
    var.append(InPortRanges)
    var.append(InIpRanges)
    var.append(InDescriptions)

    OutProtocols = []
    OutPortRanges = []
    OutIpRanges = []
    OutDescriptions = []
    for IpPermission in sg['IpPermissionsEgress']:
        try:
            if IpPermission['IpProtocol'] == '-1':
                OutProtocols.append('すべて')
            else:
                OutProtocols.append(IpPermission['IpProtocol'])
        except:
            OutProtocols.append('')
        lres = len(IpPermission['IpRanges']) + len(IpPermission['UserIdGroupPairs'])
        if lres == 0:
            lres = 1
        count = 0
        for l in range(lres):
            try:
                if IpPermission['FromPort'] == IpPermission['ToPort']:
                    OutPortRanges.append(IpPermission['FromPort'])
                else:
                    OutPortRanges.append(str(IpPermission['FromPort']) + '-' + str(IpPermission['ToPort']))
            except:
                OutPortRanges.append('')
            if l < len(IpPermission['IpRanges']):
                count += 1
                try:
                    OutIpRanges.append(IpPermission['IpRanges'][l]['CidrIp'])
                    try:
                        OutDescriptions.append(IpPermission['IpRanges'][l]['Description'])
                    except:
                        OutDescriptions.append('')
                except:
                    OutIpRanges.append('')
            else:
                l = l - count
                if l < 0 :
                    l = 0
                try:
                    OutIpRanges.append(IpPermission['UserIdGroupPairs'][l]['GroupId'])
                    try:
                        OutDescriptions.append(IpPermission['UserIdGroupPairs'][l]['Description'])
                    except:
                        OutDescriptions.append('')
                except:
                    OutIpRanges.append('')

    var.append(OutProtocols)
    var.append(OutPortRanges )
    var.append(OutIpRanges)
    var.append(OutDescriptions)
    return var


def describe_sg(wb,ws):

    response = app.ec2.describe_security_groups()

    for idx,cell in enumerate(app.sg_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font
    try:
        for idx,sg in enumerate(response['SecurityGroups'],2):
            if idx == 2:
                count = idx
            else:
                count += 1
            res = sort_sg(sg)
            if len(res[5]) > len(res[9]):
                lres = len(res[5]) #Inbound
            else:
                lres = len(res[9]) #Outbound
            if lres == 0:
                lres = 1
            if lres > 1:
                for l in range(lres):
                    for i , cell in enumerate(res,1):
                        if l > 0:
                            if i > 5: #Inbound
                                try:
                                    ws.cell(row=count+l,column=i,value=cell[l]).font = app.font
                                except:
                                    pass
                        else:
                            if i > 5: #Inbound
                                ws.cell(row=count,column=i,value=cell[l]).font = app.font
                            else:
                                ws.cell(row=count,column=i,value=str(cell)).font = app.font
                count += lres - 1
            else:
                for i , cell in enumerate(res,1):
                    if i > 5: #Inbound
                        try:
                            ws.cell(row=count,column=i,value=cell[0]).font = app.font
                        except:
                            pass
                    else:
                        ws.cell(row=count,column=i,value=str(cell)).font = app.font
    except:
        pass
def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.sg_title]
    except:
        ws = wb.create_sheet(title=app.sg_title)
    describe_sg(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'sg.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)