import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app

def sort_dhcp_option(dhcp):
    var = []
    try:
        for idx, dhcp_tag in enumerate(dhcp['Tags']):
            if idx > 0:
                pass
            else:
                if dhcp_tag['Key'] == 'Name':
                    var.append(dhcp_tag['Value'])
                else:
                    var.append('')
    except:
        var.append('')
    var.append(dhcp['DhcpOptionsId'])
    for DhcpConfiguration in dhcp['DhcpConfigurations']:
        if DhcpConfiguration['Key'] == 'domain-name':
            var.append(DhcpConfiguration['Values'][0]['Value'])
        if DhcpConfiguration['Key'] == 'domain-name-servers':
            var.append(DhcpConfiguration['Values'][0]['Value'])

    return var


def describe_dhcp_options(wb,ws):

    response = app.ec2.describe_dhcp_options()

    for idx,cell in enumerate(app.dhcp_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font
    try:
        for idx,dhcp in enumerate(response['DhcpOptions'],2):
            res = sort_dhcp_option(dhcp)
            for i , cell in enumerate(res,1):
                ws.cell(row=idx,column=i,value=str(cell)).font = app.font
    except:
        pass

def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.dhcp_title]
    except:
        ws = wb.create_sheet(title=app.dhcp_title)
    describe_dhcp_options(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'dhcp.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)