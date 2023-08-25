dyna__author__ = 'yashi.bindal@blazeclan.com'
import json
import traceback
from os import getenv
import boto3
import infosec
from boto3.dynamodb.conditions import Key
import ast

dyndb = boto3.resource('dynamodb', region_name='ap-south-1')
consolidated_tbl_wtd = getenv('wtd_consolidated_tbl_name')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    print(json.dumps(event))
    # [-] INFOSEC validation
    # api_event, flag = infosec.validate_request(event)

    flag = True
    if flag:
        # action_event = event["body-json"]
        action_event= event
        try:
            event_meta = action_event['meta']
            week_range = action_event.get("Week", None)
            if event_meta['EventType'] == 'Manager':
                user_id= action_event['UserId']
                action_event.pop("meta")
                res = False
                user_hierarchy=get_user_hierarchy_S3(user_id)
                res=send_hierarchy_data(action_event,user_hierarchy, week_range)
                print(res)
                return res

        except Exception as error:
            print(error)
            print("----> Required attributes are not acceptable, please check your request <----")
            return {
                'statusCode': 400,
                'Message': 'Required attributes are not acceptable, please check your request'
            }

    else:
        return event


def convert_int(val):
    try:
        val = int(val)
    except Exception as error:
        print(error)
    return val

def get_user_hierarchy_S3(user_id):
    user_hier_bucket = getenv('s3_user_hierarchy_bucket')
    user_hier_path_s3 = f"{user_id}/user_sap_hierarchy/hierarchy_tree.json"
    result = s3.get_object(Bucket=user_hier_bucket, Key=user_hier_path_s3)
    hierarchy = ast.literal_eval(result["Body"].read().decode())
    print("hierarchy from s3",hierarchy)
    hierarchy_dict={}
    hierarchy_dict['id']=hierarchy['id']
    hierarchy_dict['name']=hierarchy['Name']
    hierarchy_dict['reportees']=[]
    if len(hierarchy['reportees'])!=0:
        for reportee in hierarchy['reportees']:
            # print("Level 1")
            reportee['name']=reportee.pop('Name')
            if len(reportee['reportees'])!=0:
                for sub_reportee in reportee['reportees']:
                    # print("level 2")
                    sub_reportee.pop('reportees')
                    sub_reportee['name']=sub_reportee.pop('Name')
                    sub_reportee['reportees']=[]
                    hierarchy_dict['reportees'].append(reportee)
            else:
                print("user does not have 2nd level reportee")
                hierarchy_dict['reportees'].append(reportee)
    else:
        print("This user does not have any reportees")
    print("hierarchy_dict:--",hierarchy_dict)
    return hierarchy_dict



def send_hierarchy_data(process_event, user_hierarchy, week_range=None):
    print("----> Start Processing data <----")

    res = {}
    try:
        res['RequestMeta'] = process_event
        src_map_id = process_event['SourceMapId']

        if src_map_id != "All":
            src_map_id_spl = src_map_id.split('|')
            if len(src_map_id_spl) == 3:
                src_id_to_concat = src_map_id_spl[0] + '|' + src_map_id_spl[2]
            else:
                src_id_to_concat = src_map_id_spl[0]

            week_date = week_range + '|' + src_id_to_concat

            print("Data fetching for ", week_date)
        else:
            week_date = week_range

        res['user_hierarchy_data']={}
        metric_names = ['lead_status_positive_closure', 'lead_status_negative_closure', 'lead_status_follow_up_met',
                            'total_leads', 'lead_status_new_met']
        if 'reportees' in user_hierarchy:
            for reportee in user_hierarchy['reportees']:
                user_meta, user_count = query_table(consolidated_tbl_wtd, "user_id", reportee['id'],
                                                    "source_key",
                                                    week_date, skey=True)
                # print("user meta level 1", user_meta)
                if user_count == 1:
                    # print("in if")
                    reportee['data']= {}
                    for i in metric_names:
                        try:
                            reportee['data'][i] = len(list(user_meta[0][i].keys()))
                        except:
                            reportee['data'][i] = 0
                else:
                    reportee['data'] = {}
                    for i in metric_names:
                        reportee['data'][i] = 0
                  
                if 'reportees' in reportee:
                    for sub_reportee in reportee['reportees']:
                        user_meta, user_count = query_table(consolidated_tbl_wtd, "user_id", sub_reportee['id'],
                                                            "source_key",
                                                            week_date, skey=True)
                        # print("user meta level 2", user_meta)
                        if user_count == 1:
                            # print("in if")
                            sub_reportee['data']= {}
                            for i in metric_names:
                                try:
                                    sub_reportee['data'][i] = len(list(user_meta[0][i].keys()))
                                except:
                                    sub_reportee['data'][i] = 0
                        else:
                            sub_reportee['data']= {}
                            for i in metric_names:
                                sub_reportee['data'][i] = 0
                            
            res["user_hierarchy_data"]= user_hierarchy
            # print("hierarchy data",(user_hierarchy))
        res['statusCode'] = 200
        return res
    except:
        traceback.print_exc()
        res['statusCode'] = 501
        res['Message'] = 'Internal Server Error: Required Attributes Not Provided'

    return res


def query_table(foo_table_str, primary_key_attribute, primary_key, secondary_key_attribute="", secondary_key="",
                gsi=False, skey=False):
    foo_table = dyndb.Table(foo_table_str)
    if gsi:  # FOR GSI
        response = foo_table.query(IndexName=primary_key_attribute,
                                   KeyConditionExpression=Key(primary_key_attribute.split("-")[0]).eq(primary_key))
    elif skey:  # FOR PK SK
        response = foo_table.query(
            KeyConditionExpression=Key(primary_key_attribute).eq(primary_key) & Key(secondary_key_attribute).eq(
                secondary_key))
    else:  # FOR PK
        response = foo_table.query(KeyConditionExpression=Key(primary_key_attribute).eq(primary_key))

    response_items = response.get('Items', [])
    count_items = response.get("Count")

    return response_items, count_items
