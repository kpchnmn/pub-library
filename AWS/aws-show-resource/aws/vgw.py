import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app

def sort_vgw(vgw):
    var = []
    if len(vgw['Tags']) == 1 :
        for vgw_tag in vgw['Tags']:
            if vgw_tag['Key'] == 'Name':
                var.append(vgw_tag['Value'])
    else:
        var.append('')
    var.append(vgw['VpnGatewayId'])
    try:
        var.append(vgw['VpcAttachments'][0]['State'])
    except:
        var.append('detached')
    try:
        var.append(vgw['VpcAttachments'][0]['VpcId'])
    except:
        var.append('')
    try:
        var.append(vgw['AmazonSideAsn'])
    except:
        var.append('')
    try:
        var.append(vgw['Type'])
    except:
        var.append('')
    return var


def describe_vgw(wb,ws):

    response = app.ec2.describe_vpn_gateways()

    for idx,cell in enumerate(app.vgw_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font
    try:
        for idx,vgw in enumerate(response['VpnGateways'],2):
            res = sort_vgw(vgw)
            for i , cell in enumerate(res,1):
                ws.cell(row=idx,column=i,value=str(cell)).font = app.font
    except:
        pass

def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.vgw_title]
    except:
        ws = wb.create_sheet(title=app.vgw_title)
    describe_vgw(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'vgw.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)