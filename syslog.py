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

        print("Response code: {}".format(server_response.status_code))
        return server_response.status_code, json.loads(server_response.text)

    def set_syslog_server(self,ip,port,server):
        address_dto = {"ip":ip,"port":int(port)}
        server_dto = {"address":address_dto,"server_type":"PRIMARY"}
        resources_dto = {"usage_type":"NOTIFICATION","server_info":server_dto,"vendor_name":"syslog"}
        spec_dto = {"description":server,"resources":resources_dto,"name":server}
        metadata_dto = {"kind":"partner_server"}
        set_syslog_server_dto = {"spec":spec_dto,"api_version":"3.0","metadata":metadata_dto}
        rest_status,response = self.rest_call(POST,'partner_servers',json.dumps(set_syslog_server_dto))
        #print json.dumps(set_syslog_server_dto)
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

        #Set syslog server
        status,partner_server = rest_api.set_syslog_server("172.16.10.1","514","syslog_server_1")

        print("=" * 79)

    except Exception as ex:
        print(ex)
        exit(1)
