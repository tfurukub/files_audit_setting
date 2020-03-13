##############################################################################
#
#  Script: Remove policies via REST API (v3)
#  Author: Takeo Furukubo
#  Description: Remove policies
#  Language: Python2.7
#
##############################################################################

import pprint
import json
import requests
import sys


# v1_BASE_URL = 'https://{}:9440/PrismGateway/services/rest/v1/'
# self.v1_url = v1_BASE_URL.format(self.cluster_ip)
v3_BASE_URL = 'https://{}:9440/api/nutanix/v3/'
POST = 'post'
GET = 'get'
DELETE = 'delete'


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
        elif method_type == DELETE:
            request_url = self.v3_url + sub_url
            server_response = self.session.delete(request_url)
        else:
            print("method type is wrong!")
            return

        #print("Response code: {}".format(server_response.status_code))
        if server_response.text == "":
            return server_response.status_code,server_response.text
        else:
            return server_response.status_code, json.loads(server_response.text)

    def get_policy(self):
        rest_status,response = self.rest_call(POST,'notification_policies/list','{}')
        return rest_status,response

    def delete_policy(self,uuid):
        rest_status,response = self.rest_call(DELETE,'notification_policies/'+uuid,'{}')

        return rest_status,response

if __name__ == "__main__":
    try:
        pp = pprint.PrettyPrinter(indent=2)

        # Establish connection with a specific NTNX Cluster
        tgt_fsvm_ip = ""  # Please specify a target cluster external IP Address
        tgt_username = ""  # Please specify a user name of target cluster
        tgt_password = ""  # Please specify the password of the user

        rest_api = NtnxRestApi(tgt_fsvm_ip, tgt_username, tgt_password)

        #Get Policy
        status,response = rest_api.get_policy()

        #Check Policy Name
        args = sys.argv
        policy_name = []
        for entity in response.get('entities'):
            policy_name.append(entity.get('status').get('name'))

        if len(args) == 2:
            remove_name = args[1]
            if remove_name not in policy_name:
                print("{} doesn't exist".format(remove_name))
                exit(1)

        #Delete Policy
        for entity in response.get('entities'):
            uuid = entity.get('metadata').get('uuid')
            name = entity.get('status').get('name')
            if len(args) == 2:
                if name == remove_name:
                    print("Remove {}".format(name))
                    status,response = rest_api.delete_policy(uuid)

            elif len(args) == 1:
                print("Remove {}".format(name))
                status,response = rest_api.delete_policy(uuid)

        if status != 202:
            print("Failed to remove {} Reason = {}").format(name,response)
        
    except Exception as ex:
        print(ex)
        exit(1)
