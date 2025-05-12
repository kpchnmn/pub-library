import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app
from pprint import pprint

def sort_cvep(cvep):
    var = []
    if len(cvep['Tags']) == 1 :
        for cvep_tag in cvep['Tags']:
            if cvep_tag['Key'] == 'Name':
                var.append(cvep_tag['Value'])
    else:
        var.append('')
    var.append(cvep['InternetGatewayId'])
    try:
        var.append(cvep['Attachments'][0]['VpcId'])
    except:
        var.append('')

    return var


def describe_cvep(wb,ws):

    response = app.ec2.describe_client_vpn_endpoints()
    #pprint(response)

    for idx,cell in enumerate(app.cvep_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font

    try:
        for idx,cvep in enumerate(response['ClientVpnEndpoints'],2):
            res = sort_cvep(cvep)
            for i , cell in enumerate(res,1):
                ws.cell(row=idx,column=i,value=str(cell)).font = app.font
    except:
        pass

def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.cvep_title]
    except:
        ws = wb.create_sheet(title=app.cvep_title)
    describe_cvep(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'cvep.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)