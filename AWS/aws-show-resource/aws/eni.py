import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app

def sort_eni(eni):

    var = []
    if len(eni['TagSet']) >= 0 :
        for eni_tag in eni['TagSet']:
            if eni_tag['Key'] == 'Name':
                var.append(eni_tag['Value'])
    else:
        var.append('')
    if len(var) < 1:
        var.append('')
    try:
        var.append(eni['NetworkInterfaceId'])
    except:
        var.append('')
    try:
        var.append(eni['VpcId'])
    except:
        var.append('')
    try:
        var.append(eni['SubnetId'])
    except:
        var.append('')
    try:
        var.append(eni['AvailabilityZone'])
    except:
        var.append('')
    try:
        var.append(eni['PrivateIpAddress'])
    except:
        var.append('')
    try:
        var.append(eni['MacAddress'])
    except:
        var.append('')
    try:
        var.append(eni['Description'])
    except:
        var.append('')
    try:
        var.append(eni['Attachment']['AttachmentId'])
    except:
        var.append('')
    try:
        var.append(eni['SourceDestCheck'])
    except:
        var.append('')

    return var

def describe_enis(wb,ws):

    response = app.ec2.describe_network_interfaces()

    for idx,cell in enumerate(app.eni_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font

    try:
        for idx, eni in enumerate(response['NetworkInterfaces'],2):
            res = sort_eni(eni)
            for i , cell in enumerate(res,1):
                ws.cell(row=idx,column=i,value=str(cell)).font = app.font
    except:
        pass


def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.eni_title]
    except:
        ws = wb.create_sheet(title=app.eni_title)
    describe_enis(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'eni.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)