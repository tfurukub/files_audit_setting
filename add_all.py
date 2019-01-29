##############################################################################
#
#  Script: Create VMs on Nutanix Cluster via REST API (v2)
#  Author: Yukiya Shimizu
#  Description: Create VMs on Nutanix Cluster with Cloud-Init
#  Language: Python3
#
##############################################################################

import pprint
import json
import yaml
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

    def set_audit_log(self,partner_server,policy_name):
        partner_server_reference_list_dto = []
        for entity in partner_server:
            partner_server_reference_list_dto = partner_server_reference_list_dto + [{"kind":"partner_server","uuid":partner_server[entity]}]
        file_operation_list_dto = ["FILE_CREATE","FILE_DELETE","FILE_READ","FILE_WRITE","FILE_OPEN","FILE_CLOSE","DIRECTORY_CREATE","DIRECTORY_DELETE","RENAME","SETATTR","SYMLINK_CREATE","LINK_CREATE","SECURITY"]
        protocol_type_list_dto = ["SMB"]
        resources_dto = {"partner_server_reference_list":partner_server_reference_list_dto,"file_operation_list":file_operation_list_dto,"protocol_type_list":protocol_type_list_dto,"all_mount_targets":True}
        spec_dto = {"name":policy_name,"resources":resources_dto,"description":policy_name}
        metadata_dto = {"kind": "notification_policy","spec_version": 0}
        set_audit_log_dto = {"spec":spec_dto,"api_version": "3.0","metadata":metadata_dto}
        print json.dumps(set_audit_log_dto)
        rest_status,response = self.rest_call(POST,'notification_policies',json.dumps(set_audit_log_dto))
        return rest_status,response
        

if __name__ == "__main__":
    try:
        pp = pprint.PrettyPrinter(indent=2)

        # Establish connection with a specific NTNX Cluster
        tgt_fsvm_ip = "172.16.100.21"  # Please specify a target cluster external IP Address
        tgt_username = "admin"  # Please specify a user name of target cluster
        tgt_password = "Nutanix/4u"  # Please specify the password of the user

        rest_api = NtnxRestApi(tgt_fsvm_ip, tgt_username, tgt_password)

        #Get syslog server
        status,response = rest_api.get_syslog()
        if status != 200:
            print("Get syslog server error: {}".format(status))
            exit(1)
        syslog_server = {}
        for entity in response.get("entities"):
            syslog_server[entity.get('status').get('name')] = entity.get('metadata').get('uuid')
        args = sys.argv
        #Turn On Audit Log for specified share 
        if len(args) == 2:
            print("Send syslog to all syslog server")
            status,response = rest_api.set_audit_log(syslog_server,args[1])
        elif len(args) == 3:
            if syslog_server.has_key(args[3]) == False:
                print("Syslog server {} doesn't exist".format(args[3]))
                exit(1)
            print("Send syslog to {}".format(args[3]))
            syslog_server_single = {}
            syslog_server_single[args[3]] = syslog_server[args[3]]
            status,response = rest_api.set_audit_log(mount_target[args[1]],args[2])
        elif len(args) > 4:
            print("too many parameters")

        if status != 202:
            print("Turn On Audit Log error: {},response = {}".format(status,response))
            exit(1)

    except Exception as ex:
        print(ex)
        exit(1)
