import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app

def sort_ngw(ngw):
    var = []
    if len(ngw['Tags']) == 1 :
        for ngw_tag in ngw['Tags']:
            if ngw_tag['Key'] == 'Name':
                var.append(ngw_tag['Value'])
    else:
        var.append('')
    var.append(ngw['NatGatewayId'])
    var.append(ngw['VpcId'])
    var.append(ngw['SubnetId'])
    try:
        var.append(ngw['NatGatewayAddresses'][0]['PrivateIp'])
    except:
        var.append('')
    try:
        var.append(ngw['NatGatewayAddresses'][0]['PublicIp'])
    except:
        var.append('')
    try:
        var.append(ngw['NatGatewayAddresses'][0]['NetworkInterfaceId'])
    except:
        var.append('')
    return var


def describe_ngw(wb,ws):

    response = app.ec2.describe_nat_gateways()
    for idx,cell in enumerate(app.ngw_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font

    try:
        for idx,ngw in enumerate(response['NatGateways'],2):
            res = sort_ngw(ngw)
            for i , cell in enumerate(res,1):
                ws.cell(row=idx,column=i,value=str(cell)).font = app.font
    except:
        pass


def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.ngw_title]
    except:
        ws = wb.create_sheet(title=app.ngw_title)
    describe_ngw(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'ngw.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)