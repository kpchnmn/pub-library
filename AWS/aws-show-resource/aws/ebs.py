import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app

def sort_ebs(ebs):

    var = []
    if len(ebs['Tags']) >= 0 :
        for ebs_tag in ebs['Tags']:
            if ebs_tag['Key'] == 'Name':
                var.append(ebs_tag['Value'])
    else:
        var.append('')
    if len(var) < 1:
        var.append('')
    try:
        var.append(ebs['VolumeId'])
    except:
        var.append('')
    try:
        var.append(ebs['Attachments'][0]['InstanceId'])
    except:
        var.append('')
    try:
        var.append(ebs['Size'])
    except:
        var.append('')
    try:
        var.append(ebs['VolumeType'])
    except:
        var.append('')
    try:
        var.append(ebs['Iops'])
    except:
        var.append('')
    try:
        var.append(ebs['Encrypted'])
    except:
        var.append('')
    try:
        var.append(ebs['AvailabilityZone'])
    except:
        var.append('')

    return var

def describe_ebss(wb,ws):

    response = app.ec2.describe_volumes()

    for idx,cell in enumerate(app.ebs_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font

    try:
        for idx, ebs in enumerate(response['Volumes'],2):
            res = sort_ebs(ebs)
            for i , cell in enumerate(res,1):
                ws.cell(row=idx,column=i,value=str(cell)).font = app.font
    except:
        pass

def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.ebs_title]
    except:
        ws = wb.create_sheet(title=app.ebs_title)
    describe_ebss(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'ebs.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)