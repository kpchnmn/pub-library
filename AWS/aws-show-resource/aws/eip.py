import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app

def sort_eip(eip):
    var = []
    try:
        for idx,eip_tag in enumerate(eip['Tags']):
            if idx > 0:
                pass
            else:
                if eip_tag['Key'] == 'Name':
                    var.append(eip_tag['Value'])
                else:
                    var.append('')
    except:
        var.append('')
    try:
        var.append(eip['PrivateIpAddress'])
    except:
        var.append('')
    var.append(eip['PublicIp'])
    try:
        var.append(eip['AllocationId'])
    except:
        var.append('')
    try:
        var.append(eip['AssociationId'])
    except:
        var.append('')
    try:
        var.append(eip['InstanceId'])
    except:
        var.append('-')
    try:
        var.append(eip['NetworkInterfaceId'])
    except:
        var.append('')

    return var


def describe_eip(wb,ws):

    response = app.ec2.describe_addresses()

    for idx,cell in enumerate(app.eip_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font
    try:
        for idx,eip in enumerate(response['Addresses'],2):
            res = sort_eip(eip)
            for i , cell in enumerate(res,1):
                ws.cell(row=idx,column=i,value=str(cell)).font = app.font
    except:
        pass

def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.eip_title]
    except:
        ws = wb.create_sheet(title=app.eip_title)
    describe_eip(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'eip.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)