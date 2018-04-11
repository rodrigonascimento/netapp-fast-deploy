#!/usr/bin/python
'''NetApp Fast Deployment command-line
'''

import sys
import json
import argparse
import time
sys.path.append('./lib')
from ontap import ClusterSession, Aggregate, Svm, LogicalInterface, InitiatorGroup, Volume, Lun

def timestamp():
    '''Getting a timestamp to log messages
    '''
    return time.strftime('%Y-%m-%d %H:%M:%S --')

def load_to_dict(json_file):
    '''Loading a json file into a python dictionary
    '''
    with open(json_file, 'r') as f:
        stgschema = json.load(f)
    return stgschema

def cli_args():
    '''Parsing cli arguments
    '''
    parser = argparse.ArgumentParser(description='NetApp Fast Deployment Tool')
    parser.add_argument('--storage-spec', type=str, help='Storage specification file')
    parser.add_argument('--action', choices=['deploy'], help='Actions to be executed')

    return parser.parse_args()

def deploy(cli_options):
    '''Deploying an ONTAP based storage
    '''
    stgconf = load_to_dict(cli_options.storage_spec)

    print '{} Connecting to {}'.format(timestamp(), stgconf['auth']['cluster-ip'])
    ntapcluster = ClusterSession(stgconf['auth']['cluster-ip'], stgconf['auth']['user'], stgconf['auth']['pass'])

    print '{} Validating node names:'.format(timestamp())
    cluster_nodes = ntapcluster.get_nodes()
    if type(cluster_nodes) == list:
        for cn in cluster_nodes:
            if cn == stgconf['aggregates'][cluster_nodes.index(cn)]['node-name']:
                print '{}   Node name {} matches your storage specification file'.format(timestamp(), cn)
            else:
                print '{}   Node name {} does not match the node name in your storage specification file [ {} ]'.format(timestamp(), cn, stgconf['aggregates'][cluster_nodes.index(cn)]['node-name'])
                sys.exit(1)
    elif type(cluster_nodes) == tuple:
        print '{} Validating node names has {}'.format(timestamp(), cluster_nodes[0])
        print '{} Error: {}'.format(timestamp(), cluster_nodes[1])
        sys.exit(1)

    print '{} Preparing to create aggregates:'.format(timestamp())
    aggr_objs = []
    for doc in stgconf['aggregates']:
        print '  Aggregate....: %s' % doc['aggregate-name']
        print '    Node Name  : %s' % doc['node-name']
        print '    Disk count : %d' % doc['disk-count']
        print '    Disk type  : %s' % doc['disk-type']
        print '    RAID type  : %s' % doc['raid-type']
        print '    RAID size  : %d' % doc['raid-size']
        print ''
        #-- Creating a list of Aggregate instances
        aggr_objs.append(Aggregate(doc))

    #-- Creating Aggregates
    for aggr in aggr_objs:
        rc = aggr.create(ntapcluster)
        if rc[0] == 'failed':
            print '{} Warning: {}'.format(timestamp(), rc[1])
        elif rc[0] == 'passed':
            print '{} Aggregate {} created successfully'.format(timestamp(), aggr.aggr_name)

    #-- Creating a SVM instance
    print '{} Preparing to create SVMs: '.format(timestamp())
    print '{} {} SVM(s) will be created: '.format(timestamp(), len(stgconf['svm']))

    for doc_svm in stgconf['svm']:
        #-- tunneling for vserver commands
        ntapsvm = ClusterSession(stgconf['auth']['cluster-ip'], stgconf['auth']['user'], stgconf['auth']['pass'], doc_svm['name'])
        print '  SVM..............: {}'.format(doc_svm['name'])
        print '    Root volume    : {}'.format(doc_svm['name'] + '_root')
        print '    Aggregate      : {}'.format(doc_svm['aggr-list'][0])
        print '    Security Style : {}'.format(doc_svm['security-style'])
        print '    Aggr-list      : {}'.format(doc_svm['aggr-list'])
        print '    Protocols      : {}'.format(doc_svm['protocols'])
        print ''
        svm = Svm(doc_svm)

        #-- Creating SVM
        rc = svm.create(ntapcluster)
        if rc[0] == 'failed':
            print '{} Warning: {}'.format(timestamp(), rc[1])
        elif rc[0] == 'passed':
            time.sleep(10)
            print '{} SVM {} created successfully'.format(timestamp(), svm.vserver_name)

        #-- Setting SVM properties
        rc = svm.set_properties(ntapcluster)
        if rc[0] == 'failed':
            print '{} Warning: {}'.format(timestamp(), rc[1])
        elif rc[0] == 'passed':
            print '{} SVM {} properties configured successfully'.format(timestamp(), svm.vserver_name)

        #-- Creating a list of LIF instances
        print '{} Preparing to create Logical Interfaces for SVM {}'.format(timestamp(), doc_svm['name'])
        print '{} {} logical interfaces will be created:'.format(timestamp(), len(doc_svm['network']))
        lif_objs = []
        for doc_lif in doc_svm['network']:
            doc_lif['vserver'] = doc_svm['name']
            if (doc_lif['data-protocol'] == 'none') or (doc_lif['data-protocol'] == 'nfs') or (doc_lif['data-protocol'] == 'cifs') or (doc_lif['data-protocol'] == 'iscsi'):
                print '  LIF Name.........: {}'.format(doc_lif['lif-name'])
                print '    IP Address     : {}'.format(doc_lif['ip-addr'])
                print '    Netmask        : {}'.format(doc_lif['netmask'])
                print '    Role           : {}'.format(doc_lif['role'])
                print '    Home Node      : {}'.format(doc_lif['home-node'])
                print '    Home Port      : {}'.format(doc_lif['home-port'])
                print '    Data Protocol  : {}'.format(doc_lif['data-protocol'])
                print ''
            elif (doc_lif['data-protocol'] == 'fcp'):
                print '  LIF Name.........: {}'.format(doc_lif['lif-name'])
                print '    Role           : {}'.format(doc_lif['role'])
                print '    Home Node      : {}'.format(doc_lif['home-node'])
                print '    Home Port      : {}'.format(doc_lif['home-port'])
                print '    Data Protocol  : {}'.format(doc_lif['data-protocol'])
                print ''
            lif_objs.append(LogicalInterface(doc_lif))

        #-- Creating LIFs
        for lif in lif_objs:
            rc = lif.create(ntapcluster)
            if rc[0] == 'failed':
                print '{} Warning: {}'.format(timestamp(), rc[1])
            elif rc[0] == 'passed':
                print '{} LIF {} created successfully'.format(timestamp(), lif.interface_name)

        # -- Creating a list of igroup instances, if they exists
        if 'igroups' in doc_svm.keys():
            print '{} Preparing to create igroups for SVM {}'.format(timestamp(), doc_svm['name'])
            print '{} {} igroup(s) will be created: '.format(timestamp(), len(doc_svm['igroups']))
            ig_objs = []
            for doc_ig in doc_svm['igroups']:
                print '  Igroup Name      : {}'.format(doc_ig['igroup-name'])
                print '    Igroup Type    : {}'.format(doc_ig['igroup-type'])
                print '    Initiator List : {}'.format(doc_ig['initiator-list'])
                ig_objs.append(InitiatorGroup(doc_ig))

            for igroup in ig_objs:
                rc = igroup.create(ntapsvm)
                if rc[0] == 'failed':
                    print '{} Warning: {}'.format(timestamp(), rc[1])
                elif rc[0] == 'passed':
                    print '{} igroup {} created successfully'.format(timestamp(), igroup.initiator_group_name)

                rc = igroup.add_initiators(ntapsvm)
                for initiator_rc in rc:
                    if initiator_rc[0] == 'failed':
                        print '{} Warning: {}'.format(timestamp(), initiator_rc[1])
                    elif initiator_rc[0] == 'passed':
                        print '{} initiator {} added to igroup {} successfully'.format(timestamp(), initiator_rc[3], initiator_rc[2])

        #-- Volumes & LUNS
        print '{} Preparing to create volume(s) for SVM {}'.format(timestamp(), doc_svm['name'])
        total_volumes = 0
        for doc_vol in doc_svm['volumes']:
            total_volumes += doc_vol['vol-quantity']
        print '{} {} volume(s) will be created: '.format(timestamp(), total_volumes)

        for doc_vol in doc_svm['volumes']:
            if 'luns' in doc_vol.keys():
                luns_per_vol = doc_vol['luns']['lun-quantity'] / doc_vol['vol-quantity']
                if luns_per_vol == 0:
                    luns_per_vol = 1


            dv = 0
            while dv < doc_vol['vol-quantity']:
                #-- Creating volume instance
                vol_spec = {}
                if dv <= 9:
                    vol_spec['volume'] = doc_vol['vol-name']+'0'+str(dv)
                else:
                    vol_spec['volume'] = doc_vol['vol-name']+str(dv)
                vol_spec['containing-aggr-name'] = doc_vol['aggr-list'][(dv % len(doc_vol['aggr-list']))]
                vol_spec['volume-type'] = doc_vol['volume-type']
                vol_spec['volume-security-style'] = doc_vol['security-style']
                vol_spec['snapshot-policy'] = doc_vol['snapshot-policy']
                vol_spec['percentage-snapshot-reserve'] = doc_vol['pct-snapshot-reserve']
                vol_spec['efficiency-policy'] = doc_vol['efficiency-policy']
                if doc_vol['pct-snapshot-reserve'] == 0:
                    vol_spec['size'] = int(doc_vol['vol-size-gb']*1024*1024*1024)
                elif doc_vol['pct-snapshot-reserve'] > 0:
                    vol_spec['size'] = int(doc_vol['vol-size-gb']*1024*1024*1024) - int((doc_vol['vol-size-gb']*1024*1024*1024)*doc_vol['pct-snapshot-reserve']/100)

                vol = Volume(vol_spec)
                rc = vol.create(ntapsvm)
                if rc[0] == 'failed':
                    print '{} Warning: {}'.format(timestamp(), rc[1])
                elif rc[0] == 'passed':
                    print '{} Volume {} created successfully'.format(timestamp(), vol.volume)

                if 'luns' in doc_vol.keys():
                    dl = 0
                    while dl < luns_per_vol:
                        lun_spec = {}
                        if dl <= 9:
                            lun_spec['path'] = '/vol/'+vol_spec['volume']+'/'+doc_vol['luns']['lun-name']+'0'+str(dl)
                        else:
                            lun_spec['path'] = '/vol/'+vol_spec['volume']+'/'+doc_vol['luns']['lun-name']+str(dl)

                        lun_spec['size'] = int((vol_spec['size'] - 1073741824)/luns_per_vol)
                        lun_spec['ostype'] = doc_vol['luns']['os-type']
                        lun_spec['space-reservation-enabled'] = doc_vol['luns']['space-reservation-enabled']
                        lun_spec['space-allocation-enabled'] = doc_vol['luns']['space-allocation-enabled']
                        if doc_vol['luns']['map-to-all']:
                            lun_spec['igroup-name'] = doc_vol['luns']['igroup']
                        else:
                            no_map_to_all = []
                            no_map_to_all.append(doc_vol['luns']['igroup'][dl % len(doc_vol['luns']['igroup'])])
                            lun_spec['igroup-name'] = no_map_to_all

                        lun = Lun(lun_spec)
                        rc = lun.create(ntapsvm)
                        if rc[0] == 'failed':
                            print '{} Warning: {}'.format(timestamp(), rc[1])
                        elif rc[0] == 'passed':
                            print '{} LUN {} created successfully'.format(timestamp(), lun.path)

                        rc = lun.mapping(ntapsvm)
                        for lun_rc in rc:
                            if lun_rc[0] == 'failed':
                                print '{} Warning: {}'.format(timestamp(), lun_rc[1])
                            elif lun_rc[0] == 'passed':
                                print '{} LUN {} mapped to igroup {} successfully'.format(timestamp(), lun_rc[2], lun_rc[3])

                        dl += 1
                dv += 1

def main():
    cmd_args = cli_args()

    if 'deploy' in cmd_args.action:
        deploy(cmd_args)


if __name__ == '__main__':
    main()
