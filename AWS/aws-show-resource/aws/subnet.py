import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app

def sort_subnet(subnet):
    var = []
    try:
        for idx, subnet_tag in enumerate(subnet['Tags']):
            if idx > 0:
                pass
            else:
                if subnet_tag['Key'] == 'Name':
                    var.append(subnet_tag['Value'])
                else:
                    var.append('')
    except:
        var.append('')
    var.append(subnet['SubnetId'])
    var.append(subnet['CidrBlock'])
    var.append(subnet['AvailabilityZone'])
    var.append(subnet['DefaultForAz'])
    var.append(subnet['MapPublicIpOnLaunch'])
    var.append(subnet['VpcId'])

    return var

def describe_subnet(wb,ws):

    response = app.ec2.describe_subnets()

    for idx,cell in enumerate(app.subnet_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font

    try:
        for idx,subnet in enumerate(response['Subnets'],2):
            res = sort_subnet(subnet)
            for i , cell in enumerate(res,1):
                ws.cell(row=idx,column=i,value=str(cell)).font = app.font
    except:
        pass

def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.subnet_title]
    except:
        ws = wb.create_sheet(title=app.subnet_title)
    describe_subnet(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'subnet.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)