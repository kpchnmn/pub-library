import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app

def sort_route(route):
    var = []
    if len(route['Tags']) == 1 :
        for route_tag in route['Tags']:
            if route_tag['Key'] == 'Name':
                var.append(route_tag['Value'])
    else:
        var.append('')
    var.append(route['RouteTableId'])
    var.append(route['VpcId'])
    if len(route['PropagatingVgws']) == 0 :
        var.append('いいえ')
    else:
        var.append(route['PropagatingVgws'][0]['GatewayId'])
    var.append(route['Associations'][0]['Main'])
    routetable_associations = []
    for association in route['Associations']:
        try:
            routetable_associations.append(association['SubnetId'])
        except:
            routetable_associations.append('')
    var.append(routetable_associations)
    routes = []
    for rt in route['Routes']:
        try:
            routes.append(rt['DestinationCidrBlock'])
        except:
            routes.append(rt['DestinationPrefixListId'])
    var.append(routes)
    routes = []
    for rt in route['Routes']:
        try:
            routes.append(rt['GatewayId'])
        except:
            try:
                routes.append(rt['NatGatewayId'])
            except:
                routes.append('')
    var.append(routes)
    return var

def describe_subnet(wb,ws):

    response = app.ec2.describe_route_tables()

    for idx,cell in enumerate(app.route_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font
    try:
        for idx,route in enumerate(response['RouteTables'],2):
            if idx == 2:
                count = idx
            else:
                count += 1
            res = sort_route(route)
            if len(res[5]) > len(res[6]):
                lres = len(res[5]) # SubnetID
            else:
                lres = len(res[6])
            if lres > 1:
                for l in range(lres):
                    for i , cell in enumerate(res,1):
                        if l > 0 :
                            if i > 5 : #SubnetID
                                try:
                                    ws.cell(row=count+l,column=i,value=cell[l]).font = app.font
                                except:
                                    pass
                        else:
                            if i > 5: #SubnetID
                                ws.cell(row=count,column=i,value=cell[l]).font = app.font
                            else:
                                ws.cell(row=count,column=i,value=str(cell)).font = app.font
                count += lres - 1
            else:
                for i , cell in enumerate(res,1):
                        if i > 5: #SubnetID
                            ws.cell(row=count,column=i,value=cell[0]).font = app.font
                        else:
                            ws.cell(row=count,column=i,value=str(cell)).font = app.font
    except:
        pass

def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.route_title]
    except:
        ws = wb.create_sheet(title=app.route_title)
    describe_subnet(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'route.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)