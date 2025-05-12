import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app

def sort_vpc(vpc):
    var = []
    try:
        for idx, vpc_tag in enumerate(vpc['Tags']):
            if idx > 0:
                pass
            else:
                if vpc_tag['Key'] == 'Name':
                    var.append(vpc_tag['Value'])
                else:
                    var.append('')
    except:
        var.append('')
    var.append(vpc['VpcId'])
    cidrblockassociationset = []
    for cidrblock in vpc['CidrBlockAssociationSet']:
        cidrblockassociationset.append(cidrblock['CidrBlock'])
    var.append(cidrblockassociationset)
    res1 = app.ec2.describe_vpc_attribute(Attribute='enableDnsSupport',VpcId=vpc['VpcId'])
    var.append(res1['EnableDnsSupport']['Value'])
    res2 = app.ec2.describe_vpc_attribute(Attribute='enableDnsHostnames',VpcId=vpc['VpcId'])
    var.append(res2['EnableDnsHostnames']['Value'])
    var.append(vpc['DhcpOptionsId'])
    var.append((vpc['InstanceTenancy']))
    var.append(vpc['IsDefault'])

    return var

def describe_vpcs(wb,ws):

    response = app.ec2.describe_vpcs()
    for idx,cell in enumerate(app.vpc_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font

    try:
        for idx, vpc in enumerate(response['Vpcs'],2):
            if idx == 2:
                count = idx
            else:
                count += 1
            res = sort_vpc(vpc)
            lres = len(res[2])
            if lres > 1: #CidrBlock
                for l in range(lres):
                    for i , cell in enumerate(res,1):
                        if l > 0:
                            if i == 3: #CidrBlock
                                try:
                                    ws.cell(row=count+l,column=i,value=cell[l]).font = app.font
                                except:
                                    pass
                        else:
                            if i == 3: #CidrBlock
                                ws.cell(row=count,column=i,value=cell[l]).font = app.font
                            else:
                                ws.cell(row=count,column=i,value=str(cell)).font = app.font
                count += lres - 1
            else:
                for i , cell in enumerate(res,1):
                    if i == 3: #CidrBlock
                        ws.cell(row=count,column=i,value=cell[0]).font = app.font
                    else:
                        ws.cell(row=count,column=i,value=str(cell)).font = app.font
    except:
        pass

def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.vpc_title]
    except:
        ws = wb.create_sheet(title=app.vpc_title)
    describe_vpcs(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'vpc.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)