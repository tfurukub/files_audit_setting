##############################################################################
#
#  Script: Get Syslog Configuration  via REST API (v3)
#  Author: Takeo Furukubo
#  Description: Get Syslog Configuration
#  Language: Python2.7
#
##############################################################################

import pprint
import json
import requests
import sys
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)


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

    def get_mount_targets(self):
        rest_status,response = self.rest_call(POST,'mount_targets/list','{}')
        return rest_status,response

    def get_policy(self):
        rest_status,response = self.rest_call(POST,'notification_policies/list','{}')
        return rest_status,response

if __name__ == "__main__":
    try:
        pp = pprint.PrettyPrinter(indent=2)

        # Establish connection with a specific NTNX Cluster
        tgt_fsvm_ip = ""  # Please specify a target cluster external IP Address
        tgt_username = ""  # Please specify a user name of target cluster
        tgt_password = ""  # Please specify the password of the user

        rest_api = NtnxRestApi(tgt_fsvm_ip, tgt_username, tgt_password)

        print("=" * 79)

        #Get syslog server
        status,syslog = rest_api.get_syslog()
        if status != 200:
            print("Get syslog server error: {}".format(status))
            exit(1)

        #Get mount targets
        status, target = rest_api.get_mount_targets()
        if status != 200:
            print("Get mount target error: {}".format(status))
            exit(1)

        #Get policies 
        status, policy = rest_api.get_policy()
        if status != 200:
            print("Get policy error: {}".format(status))
            exit(1)

        syslog_list = {}
        for entity in syslog.get('entities'):
            syslog_list[entity.get('metadata').get('uuid')] = entity.get('status').get('name')
            print("Syslog Server Name = {}, IP address = {}".format(entity.get('status').get('name'),entity.get('spec').get('resources').get('server_info').get('address').get('ip')))

        target_list = {}
        for entity in target.get('entities'):
            target_name = entity.get('status').get('name')
            target_list[entity.get('metadata').get('uuid')] = target_name 
            print("Share Name = {}".format(target_name))

        for entity in policy.get('entities'):
            reference = ""
            for reference_list in entity.get('status').get('resources').get('mount_target_reference_list'):
                reference = reference + target_list[reference_list.get('uuid')] + ","
            partner = ""
            for partner_list in entity.get('status').get('resources').get('partner_server_reference_list'):
                partner = partner + syslog_list[partner_list.get('uuid')] + ","
            print("Policy Name = {}, Mount Target = {} Syslog Server = {}".format(entity.get('status').get('name'),reference,partner[:-1]))

    except Exception as ex:
        print(ex)
        exit(1)
