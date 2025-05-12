import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app

def sort_igw(igw):
    var = []
    if len(igw['Tags']) == 1 :
        for igw_tag in igw['Tags']:
            if igw_tag['Key'] == 'Name':
                var.append(igw_tag['Value'])
    else:
        var.append('')
    var.append(igw['InternetGatewayId'])
    try:
        var.append(igw['Attachments'][0]['VpcId'])
    except:
        var.append('')

    return var


def describe_igw(wb,ws):

    response = app.ec2.describe_internet_gateways()

    for idx,cell in enumerate(app.igw_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font
    try:
        for idx,igw in enumerate(response['InternetGateways'],2):
            res = sort_igw(igw)
            for i , cell in enumerate(res,1):
                ws.cell(row=idx,column=i,value=str(cell)).font = app.font
    except:
        pass

def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.igw_title]
    except:
        ws = wb.create_sheet(title=app.igw_title)
    describe_igw(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'igw.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)