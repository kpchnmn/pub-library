import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app

def sort_cgw(cgw):
    var = []
    if len(cgw['Tags']) == 1 :
        for cgw_tag in cgw['Tags']:
            if cgw_tag['Key'] == 'Name':
                var.append(cgw_tag['Value'])
    else:
        var.append('')
    var.append(cgw['CustomerGatewayId'])
    try:
        var.append(cgw['IpAddress'])
    except:
        var.append('')
    try:
        var.append(cgw['BgpAsn'])
    except:
        var.append('')
    try:
        var.append(cgw['Type'])
    except:
        var.append('')

    return var


def describe_cgw(wb,ws):

    response = app.ec2.describe_customer_gateways()

    for idx,cell in enumerate(app.cgw_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font
    try:
        for idx,cgw in enumerate(response['CustomerGateways'],2):
            res = sort_cgw(cgw)
            for i , cell in enumerate(res,1):
                ws.cell(row=idx,column=i,value=str(cell)).font = app.font
    except:
        pass

def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.cgw_title]
    except:
        ws = wb.create_sheet(title=app.cgw_title)
    describe_cgw(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'cgw.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)