##############################################################################
#
#  Script: Set Policy  via REST API (v3)
#  Author: Takeo Furukubo
#  Description: Configure policy
#  Language: Python2.7
#
##############################################################################

import pprint
import json
import requests
import sys
import distutils.util


# v1_BASE_URL = 'https://{}:9440/PrismGateway/services/rest/v1/'
# self.v1_url = v1_BASE_URL.format(self.cluster_ip)
v3_BASE_URL = 'https://{}:9440/api/nutanix/v3/'
POST = 'post'
GET = 'get'


class NtnxRestApi:
    def __init__(self, cluster_ip, username, password):
        self.cluster_ip = cluster_ip
        self.username = username
        self.password = password
        self.v3_url = v3_BASE_URL.format(self.cluster_ip)
        self.session = self.get_server_session()

    def get_server_session(self):
        # Creating REST client session for server connection, after globally setting.
        # Authorization, content type, and character set for the session.

        session = requests.Session()
        session.auth = (self.username, self.password)
        session.verify = False
        session.headers.update(
            {'Content-Type': 'application/json; charset=utf-8'})
        return session

    def rest_call(self, method_type, sub_url, payload_json):
        if method_type == GET:
            request_url = self.v3_url + sub_url
            server_response = self.session.get(request_url)
        elif method_type == POST:
            request_url = self.v3_url + sub_url
            server_response = self.session.post(request_url, payload_json)
        else:
            print("method type is wrong!")
            return

        #print("Response code: {}".format(server_response.status_code))
        return server_response.status_code, json.loads(server_response.text)

    def get_syslog(self):
       rest_status,response = self.rest_call(POST,'partner_servers/list','{}')
       return rest_status,response

    def get_fileserver(self):
        rest_status,response = self.rest_call(GET,'file_servers',None)
        return rest_status,response

    def get_mount_targets(self):
        rest_status,response = self.rest_call(POST,'mount_targets/list','{}')
        return rest_status,response

    def set_audit_log(self,mount_target_uuid,syslog_uuid,policy_name):
        mount_target_reference_list_dto = []
        for entity in mount_target_uuid:
            mount_target_reference_list_dto = mount_target_reference_list_dto + [{"kind":"mount_target","uuid":entity}]

        partner_server_reference_list_dto = []
        for entity in syslog_uuid:
            partner_server_reference_list_dto = partner_server_reference_list_dto + [{"kind":"partner_server","uuid":entity}]
        file_operation_list_dto = ["FILE_CREATE","FILE_DELETE","FILE_READ","FILE_WRITE","FILE_OPEN","FILE_CLOSE","DIRECTORY_CREATE","DIRECTORY_DELETE","RENAME","SETATTR","SYMLINK_CREATE","LINK_CREATE","SECURITY"]
        protocol_type_list_dto = ["SMB"]
        resources_dto = {"mount_target_reference_list":mount_target_reference_list_dto,"partner_server_reference_list":partner_server_reference_list_dto,"file_operation_list":file_operation_list_dto,"protocol_type_list":protocol_type_list_dto}
        spec_dto = {"name":policy_name,"resources":resources_dto,"description":policy_name}
        metadata_dto = {"kind": "notification_policy","spec_version": 0}
        set_audit_log_dto = {"spec":spec_dto,"api_version": "3.0","metadata":metadata_dto}
        rest_status,response = self.rest_call(POST,'notification_policies',json.dumps(set_audit_log_dto))
        return rest_status,response
        

if __name__ == "__main__":
    try:
        pp = pprint.PrettyPrinter(indent=2)

        # Establish connection with a specific NTNX Cluster
        tgt_fsvm_ip = ""  # Please specify a target cluster external IP Address
        tgt_username = ""  # Please specify a user name of target cluster
        tgt_password = ""  # Please specify the password of the user

        rest_api = NtnxRestApi(tgt_fsvm_ip, tgt_username, tgt_password)

        #Get syslog server
        status,response = rest_api.get_syslog()
        if status != 200:
            print("Get syslog server error: {}".format(status))
            exit(1)
        syslog_server = {}
        for entity in response.get("entities"):
            syslog_server[entity.get('status').get('name')] = entity.get('metadata').get('uuid')

        #Get mount targets
        status, response = rest_api.get_mount_targets()
        if status != 200:
            print("Get mount target error: {}".format(status))
            exit(1)
        mount_target = {}
        for entity in response.get("entities"):
            mount_target[entity.get('status').get('name')] = entity.get('metadata').get('uuid')

        #Check mount target name
        args = sys.argv
        share_name = args[1]
        policy_name = args[2]
        syslog_name = args[3]
        share_name_list = share_name.strip().split(',')
        syslog_name_list = syslog_name.strip().split(',')
        mount_target_uuid = []
        syslog_uuid = []

        if len(args) < 4:
            print("Please specify share name, policy name , and syslog server name")
            print("python add_policy.py <share name> <policy name> <syslog server name>")
            exit(1)
            
        if share_name == "all_shares":
            for s in mount_target:
                mount_target_uuid.append(mount_target[s])
        else:
            for s in share_name_list:
                if mount_target.has_key(s) == False:
                    print("{} doesn't exist".format(s))
                    exit(1)
                mount_target_uuid.append(mount_target[s])


        if syslog_name == "all_syslogs":
            for s in syslog_server:
                syslog_uuid.append(syslog_server[s])
        else:
            for s in syslog_name_list:
                if syslog_server.has_key(s) == False:
                    print("{} doesn't exist".format(s))
                    exit(1)
                syslog_uuid.append(syslog_server[s])

        #Turn On Audit Log for specified share 
        status,response = rest_api.set_audit_log(mount_target_uuid,syslog_uuid,policy_name)

        if status != 202:
            print("Turn On Audit Log error: {},response = {}".format(status,response))
            exit(1)

    except Exception as ex:
        print(ex)
        exit(1)
