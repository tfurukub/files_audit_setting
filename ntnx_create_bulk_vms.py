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


# v1_BASE_URL = 'https://{}:9440/PrismGateway/services/rest/v1/'
# self.v1_url = v1_BASE_URL.format(self.cluster_ip)
v2_BASE_URL = 'https://{}:9440/PrismGateway/services/rest/v2.0/'
POST = 'post'
GET = 'get'


class NtnxRestApi:
    def __init__(self, cluster_ip, username, password):
        self.cluster_ip = cluster_ip
        self.username = username
        self.password = password
        self.v2_url = v2_BASE_URL.format(self.cluster_ip)
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
            request_url = self.v2_url + sub_url
            server_response = self.session.get(request_url)
        elif method_type == POST:
            request_url = self.v2_url + sub_url
            server_response = self.session.post(request_url, payload_json)
        else:
            print("method type is wrong!")
            return

        print("Response code: {}".format(server_response.status_code))
        return server_response.status_code, json.loads(server_response.text)

    def get_cluster_info(self):
        print("Getting cluster information for cluster {}".format(self.cluster_ip))
        rest_status, response = self.rest_call(GET, 'clusters', None)

        with open('cluster.json', 'wt') as fout:
            json.dump(response, fout, indent=2)
        return rest_status, response

    def get_containers_info(self):
        print("Getting containers information for cluster {}".format(self.cluster_ip))
        rest_status, response = self.rest_call(GET, 'storage_containers', None)

        with open('containers.json', 'wt') as fout:
            json.dump(response, fout, indent=2)
        return rest_status, response

    def get_networks_info(self):
        print("Getting networks information for cluster {}".format(self.cluster_ip))
        rest_status, response = self.rest_call(GET, 'networks', None)

        with open('networks.json', 'wt') as fout:
            json.dump(response, fout, indent=2)
        return rest_status, response

    def create_vm(self, network_uuid, container_uuid):
        pass

    def clone_vm(self, snapshot_vm_uuid, vm_name, user_data_yaml):
        print("Cloning {} VM from {}".format(vm_name, snapshot_vm_uuid))

        # Create VMCloneDTO
        vm_clone_spec_dto = {"name": vm_name}
        spec_list = [vm_clone_spec_dto]
        vm_customization_config_dto = {"userdata": user_data_yaml}

        vm_clone_dto = {'spec_list': spec_list, 'vm_customization_config': vm_customization_config_dto}

        #rest_status, response = self.rest_call(POST, "vms/{}/clone".format(snapshot_vm_uuid), json.dumps(vm_clone_dto))
        print json.dumps(vm_clone_dto)
        #return rest_status, response


class CloudConfig:
    def __init__(self, vm_num):
        self.gateway_ip = '172.16.0.1'
        self.tgt_hostname = 'bruce_centos{0:03d}.ntnx.local'.format(vm_num)
        self.tgt_host_ip = '172.16.11.{}/24'.format(vm_num)

    def get_yaml(self):
        # Set constant values in cloud-config file
        user_data = \
            {'users': [{'home': '/home/nutanix',
                        'lock-passwd': False,
                        'name': 'nutanix',
                        'plain_text_passwd': 'nutanix/4u',
                        'shell': '/bin/bash',
                        'sudo': ['ALL=(ALL) NOPASSWD:ALL']}],
             'timezone': 'Japan',
             "fqdn": self.tgt_hostname}

        # Set variable values in cloud-config file
        commands_list_1 = ['cloud-init-per', 'once', 'mynmcli', 'nmcli', 'connection', 'modify', 'System eth0',
                           'ipv4.method', 'manual', 'ipv4.address', self.tgt_host_ip, 'ipv4.gateway', self.gateway_ip,
                           'ipv4.dns', self.gateway_ip]
        commands_list_2 = ['cloud-init-per', 'once', 'mynmclidown', 'nmcli', 'connection', 'down', 'System eth0']
        commands_list_3 = ['cloud-init-per', 'once', 'mynmcliup', 'nmcli', 'connection', 'up', 'System eth0']

        user_data['bootcmd'] = [commands_list_1, commands_list_2, commands_list_3]
        return "#cloud-config\n" + yaml.dump(user_data)

if __name__ == "__main__":
    try:
        pp = pprint.PrettyPrinter(indent=2)

        # Establish connection with a specific NTNX Cluster
        tgt_cluster_ip = "172.16.10.119"  # Please specify a target cluster external IP Address
        tgt_username = "admin"  # Please specify a user name of target cluster
        tgt_password = "Nutanix/4u!"  # Please specify the password of the user

        rest_api = NtnxRestApi(tgt_cluster_ip, tgt_username, tgt_password)

        print("=" * 79)

        # Display a specific NTNX cluster information
        status, cluster = rest_api.get_cluster_info()

        for entity in cluster.get("entities"):
            print("Name: {}".format(entity.get('name')))
            print("ID: {}".format(entity.get('id')))
            print("Cluster External IP Address: {}".format(entity.get('cluster_external_ipaddress')))
            print("Number of Nodes: {}".format(entity.get('num_nodes')))
            print("Version: {}".format(entity.get('version')))
            print("Hypervisor Types: {}".format(entity.get('hypervisor_types')))
        print("=" * 79)
        rest_api.clone_vm("a","b","c")

        print("=" * 79)

    except Exception as ex:
        print(ex)
        exit(1)
