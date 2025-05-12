import sys
from pathlib import Path
# 上位階層のディレクトリをsys.pathに追加
sys.path.append(str(Path(__file__).parent.parent))
import app

def sort_nacl(nacl):
    var = []
    if len(nacl['Tags']) == 1 :
        for nacl_tag in nacl['Tags']:
            if nacl_tag['Key'] == 'Name':
                var.append(nacl_tag['Value'])
    else:
        var.append('')
    var.append(nacl['NetworkAclId'])
    var.append(nacl['IsDefault'])
    var.append(nacl['VpcId'])
    subnet_associations = []
    for association in nacl['Associations']:
        try:
            subnet_associations.append(association['SubnetId'])
        except:
            subnet_associations.append('')
    var.append(subnet_associations)
    InRuleNumbers = []
    InProtocols = []
    InCidrBlocks = []
    InRuleActions = []
    OutRuleNumbers = []
    OutProtocols = []
    OutCidrBlocks = []
    OutRuleActions = []
    for entry in nacl['Entries']:
        if entry['Egress'] == False:
            try:
                if entry['RuleNumber'] == 32767:
                    InRuleNumbers.append('*')
                else:
                    InRuleNumbers.append(entry['RuleNumber'])
            except:
                InRuleNumbers.append('')
            try:
                if entry['Protocol'] == '-1':
                    InProtocols.append('すべて')
                else:
                    InProtocols.append(entry['Protocol'])
            except:
                InProtocols.append('')
            try:
                InCidrBlocks.append(entry['CidrBlock'])
            except:
                InCidrBlocks.append('')
            try:
                InRuleActions.append(entry['RuleAction'])
            except:
                InRuleActions.append('')
        elif entry['Egress'] == True:
            try:
                if entry['RuleNumber'] == 32767:
                    OutRuleNumbers.append('*')
                else:
                    OutRuleNumbers.append(entry['RuleNumber'])
            except:
                OutRuleNumbers.append('')
            try:
                if entry['Protocol'] == '-1':
                    OutProtocols.append('すべて')
                else:
                    OutProtocols.append(entry['Protocol'])
            except:
                OutProtocols.append('')
            try:
                OutCidrBlocks.append(entry['CidrBlock'])
            except:
                OutCidrBlocks.append('')
            try:
                OutRuleActions.append(entry['RuleAction'])
            except:
                OutRuleActions.append('')
    var.append(InRuleNumbers)
    var.append(InProtocols)
    var.append(InCidrBlocks)
    var.append(InRuleActions)
    var.append(OutRuleNumbers)
    var.append(OutProtocols)
    var.append(OutCidrBlocks)
    var.append(OutRuleActions)

    return var


def describe_nacl(wb,ws):

    response = app.ec2.describe_network_acls()

    for idx,cell in enumerate(app.nacl_row,1):
        ws.cell(row=1,column=idx,value=cell).font = app.font

    try:
        for idx,nacl in enumerate(response['NetworkAcls'],2):
            if idx == 2:
                count = idx
            else:
                count += 1
            res = sort_nacl(nacl)
            if len(res[4]) > len(res[5]):
                if len(res[4]) > len(res[6]):
                    lres = len(res[4]) #SubnetID
                else:
                    lres = len(res[6]) #OutRule
            else:
                if len(res[5]) > len(res[6]):
                    lres = len(res[5]) #InRule
                else:
                    lres = len(res[6]) #OutRule
            if lres > 1:
                for l in range(lres):
                    for i , cell in enumerate(res,1):
                        if l > 0:
                            if i > 4: #SubnetID
                                try:
                                    ws.cell(row=count+l,column=i,value=cell[l]).font = app.font
                                except:
                                    pass
                        else:
                            if i > 4: #SubnetID
                                ws.cell(row=count,column=i,value=cell[l]).font = app.font
                            else:
                                ws.cell(row=count,column=i,value=str(cell)).font = app.font
                count += lres -1
            else:
                for i , cell in enumerate(res,1):
                    if i > 4: #SubnetID
                        ws.cell(row=count,column=i,value=cell[0]).font = app.font
                    else:
                        ws.cell(row=count,column=i,value=str(cell)).font = app.font
    except:
        pass

def main(filename):
    wb = app.px.load_workbook(filename)
    try:
        ws = wb[app.nacl_title]
    except:
        ws = wb.create_sheet(title=app.nacl_title)
    describe_nacl(wb,ws)
    wb.save(filename)

if __name__ == "__main__":
    filename = 'nacl.xlsx'
    app.create_file(filename)
    main(filename)
    app.delete_sheet(filename)