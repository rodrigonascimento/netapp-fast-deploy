#!/usr/bin/env python2
"""ONTAP Module :: Connect and execute admin tasks on FAS and AFF systems
"""

from NaServer import NaServer, NaElement


class ClusterSession:
    def __init__(self, cluster_ip, user, password, vserver=None):
        self.server = NaServer(cluster_ip, 1, 100)
        self.server.set_server_type('FILER')
        self.server.set_transport_type('HTTP')
        self.server.set_port(80)
        self.server.set_style('LOGIN')
        self.server.set_admin_user(user, password)
        if vserver is not None:
            self.server.set_vserver(vserver)

    def get_vserver(self):
        return self.server.get_vserver()

    def run_command(self, api):
        return self.server.invoke_elem(api)

    def get_nodes(self):
        api_call = NaElement('cluster-node-get-iter')
        output = self.run_command(api_call)
        if output.results_status() == 'failed':
            return output.results_status(), output.sprintf()
        else:
            cluster_node_info = output.children_get()
            for cni in cluster_node_info:
                if cni.has_children() == 1:
                    nodes = cni.children_get()
                    nodes_list = []
                    for n in nodes:
                        nodes_list.append(n.child_get_string('node-name'))
            return nodes_list


class Aggregate:
    def __init__(self, aggr_spec):
        self.node_name = aggr_spec['node-name']
        self.aggr_name = aggr_spec['aggregate-name']
        self.disk_count = aggr_spec['disk-count']
        self.disk_type = aggr_spec['disk-type']
        self.raid_type = aggr_spec['raid-type']
        self.raid_size = aggr_spec['raid-size']

    def create(self, cluster):
        api_call = NaElement('aggr-create')
        api_call.child_add_string('aggregate', self.aggr_name)
        api_call.child_add_string('disk-count', self.disk_count)
        api_call.child_add_string('disk-type', self.disk_type)
        api_call.child_add_string('raid-type', self.raid_type)
        api_call.child_add_string('raid-size', self.raid_size)

        api_child_nodes = NaElement('nodes')
        api_child_nodes.child_add_string('node-name', self.node_name)

        api_call.child_add(api_child_nodes)

        output = cluster.run_command(api_call)
        return output.results_status(), output.sprintf()

    def destroy(self, cluster):
        pass


class Svm:
    def __init__(self, svm_spec):
        self.vserver_name = svm_spec['name']
        self.root_volume = svm_spec['name'] + '_root'
        self.root_volume_aggregate = svm_spec['aggr-list'][0]
        self.root_volume_security_style = svm_spec['security-style']
        self.aggr_list = svm_spec['aggr-list']
        self.allowed_protocols = svm_spec['protocols']

    def create(self, cluster):
        api_call = NaElement('vserver-create-async')
        api_call.child_add_string('vserver-name', self.vserver_name)
        api_call.child_add_string('root-volume', self.root_volume)
        api_call.child_add_string('root-volume-aggregate', self.root_volume_aggregate)
        api_call.child_add_string('root-volume-security-style', self.root_volume_security_style)

        output = cluster.run_command(api_call)
        return output.results_status(), output.sprintf()

    def set_properties(self, cluster):
        api_call = NaElement('vserver-modify')
        api_call.child_add_string('vserver-name', self.vserver_name)

        api_child_aggrs = NaElement('aggr-list')
        for aggr in self.aggr_list:
            api_child_aggrs.child_add_string('aggr-name', aggr)

        api_child_protocols = NaElement('allowed-protocols')
        for protocol in self.allowed_protocols:
            api_child_protocols.child_add_string('protocol', protocol)

        api_call.child_add(api_child_aggrs)
        api_call.child_add(api_child_protocols)

        output = cluster.run_command(api_call)
        return output.results_status(), output.sprintf()

    def destroy(self, cluster):
        pass


class LogicalInterface:
    def __init__(self, lif_spec):
        self.vserver = lif_spec['vserver']
        self.data_protocol = lif_spec['data-protocol']

        if (lif_spec['data-protocol'] == 'none') or (lif_spec['data-protocol'] == 'nfs') or (lif_spec['data-protocol'] == 'cifs') or (lif_spec['data-protocol'] == 'iscsi'):
            self.interface_name = lif_spec['lif-name']
            self.role = lif_spec['role']
            self.home_node = lif_spec['home-node']
            self.home_port = lif_spec['home-port']
            self.address = lif_spec['ip-addr']
            self.netmask = lif_spec['netmask']
        elif (lif_spec['data-protocol'] == 'fcp'):
            self.interface_name = lif_spec['lif-name']
            self.role = lif_spec['role']
            self.home_node = lif_spec['home-node']
            self.home_port = lif_spec['home-port']

    def create(self, cluster):
        api_call = NaElement('net-interface-create')
        api_child_data_protocols = NaElement('data-protocols')
        api_child_data_protocols.child_add_string('data-protocol', self.data_protocol)
        api_call.child_add(api_child_data_protocols)

        api_call.child_add_string('vserver', self.vserver)

        if (self.data_protocol == 'none') or (self.data_protocol == 'nfs') or (self.data_protocol == 'cifs') or (self.data_protocol == 'iscsi'):
            api_call.child_add_string('interface-name', self.interface_name)
            api_call.child_add_string('role', self.role)
            api_call.child_add_string('home-node', self.home_node)
            api_call.child_add_string('home-port', self.home_port)
            api_call.child_add_string('address', self.address)
            api_call.child_add_string('netmask', self.netmask)
        elif (self.data_protocol == 'fcp'):
            api_call.child_add_string('interface-name', self.interface_name)
            api_call.child_add_string('role', self.role)
            api_call.child_add_string('home-node', self.home_node)
            api_call.child_add_string('home-port', self.home_port)

        output = cluster.run_command(api_call)
        return output.results_status(), output.sprintf()

    def destroy(self, cluster):
        pass


class InitiatorGroup:
    def __init__(self, ig_spec):
        self.initiator_group_name = ig_spec['igroup-name']
        self.initiator_group_type = ig_spec['igroup-type']
        self.os_type = ig_spec['os-type']
        self.initiator_list = ig_spec['initiator-list']

    def create(self, svm):
        api_call = NaElement('igroup-create')
        api_call.child_add_string('initiator-group-name', self.initiator_group_name)
        api_call.child_add_string('initiator-group-type', self.initiator_group_type)
        api_call.child_add_string('os-type', self.os_type)

        output = svm.run_command(api_call)
        return output.results_status(), output.sprintf()

    def add_initiators(self, svm):
        results = []
        for wwpn in self.initiator_list:
            api_call = NaElement('igroup-add')
            api_call.child_add_string('initiator-group-name', self.initiator_group_name)
            api_call.child_add_string('initiator', wwpn)

            output = svm.run_command(api_call)
            results.append((output.results_status(), output.sprintf(), self.initiator_group_name, wwpn))

        return results

    def destroy(self, cluster):
        pass


class Volume:
    def __init__(self, vol_spec):
        self.volume = vol_spec['volume']
        self.containing_aggr_name = vol_spec['containing-aggr-name']
        self.size = vol_spec['size']
        self.volume_type = vol_spec['volume-type']
        self.volume_security_style = vol_spec['volume-security-style']
        self.snapshot_policy = vol_spec['snapshot-policy']
        self.percentage_snapshot_reserve = vol_spec['percentage-snapshot-reserve']
        self.efficiency_policy = vol_spec['efficiency-policy']

    def create(self, svm):
        api_call = NaElement('volume-create')
        api_call.child_add_string('volume', self.volume)
        api_call.child_add_string('containing-aggr-name', self.containing_aggr_name)
        api_call.child_add_string('size', self.size)
        api_call.child_add_string('volume-type', self.volume_type)
        api_call.child_add_string('volume-security-style', self.volume_security_style)
        api_call.child_add_string('snapshot-policy', self.snapshot_policy)
        api_call.child_add_string('percentage-snapshot-reserve', self.percentage_snapshot_reserve)
        api_call.child_add_string('efficiency-policy', self.efficiency_policy)

        output = svm.run_command(api_call)
        return output.results_status(), output.sprintf()

    def destroy(self, svm):
        pass


class Lun:
    def __init__(self, lun_spec):
        self.path = lun_spec['path']
        self.size = lun_spec['size']
        self.ostype = lun_spec['ostype']
        self.space_reservation_enabled = lun_spec['space-reservation-enabled']
        self.space_allocation_enabled = lun_spec['space-allocation-enabled']
        self.igroup_name = lun_spec['igroup-name']

    def create(self, svm):
        api_call = NaElement('lun-create-by-size')
        api_call.child_add_string('path', self.path)
        api_call.child_add_string('size', self.size)
        api_call.child_add_string('ostype', self.ostype)
        api_call.child_add_string('space-reservation-enabled', self.space_reservation_enabled)
        api_call.child_add_string('space-allocation-enabled', self.space_allocation_enabled)

        output = svm.run_command(api_call)
        return output.results_status(), output.sprintf()

    def mapping(self, svm):
        results = []
        for igroup in self.igroup_name:
            api_call = NaElement('lun-map')
            api_call.child_add_string('path', self.path)
            api_call.child_add_string('initiator-group', igroup)

            output = svm.run_command(api_call)
            results.append((output.results_status(), output.sprintf(), self.path, igroup))

        return results

    def destroy(self, svm):
        pass
