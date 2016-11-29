# netapp-fast-deploy
NetApp Fast Deployment Tool

You can have your NetApp AFF Storage deployed in minutes using this tool.

All you need is a storage-spec file, access to the NetApp Support website to download the NetApp Manageability Software Development Kit (NMSDK) and a coffee machine that would be able to brew your coffee in less than 1 minute.

The tool is ready to deploy FCP and iSCSI environments and after a few more lines of code it will be ready to deploy NFS and CIFS environments too.

## What is a storage-spec file?
It's a JSON file that describes your storage environment regarding to Aggregates, SVMs, LIFs, Volumes and LUNs.

## How a storage-spec file looks like?
You will have one storage-spec file per cluster that you would like to deploy using this tool. Key names used in this file are self explanatory for those that are familiar with ONTAP.
```
{
    "auth" : {
        "cluster-ip" : "",
        "user"       : "",
        "pass"       : ""
    },
    "aggregates" : [
        {
            "aggregate-name" : "",
            "node-name"      : "",
            "disk-count"     : 0,
            "disk-type"      : "",
            "raid-type"      : "",
            "raid-size"      : 0
        }
    ],
    "svm" : [
        {
            "name"           : "",
            "security-style" : "",
            "protocols"      : [ "" ],
            "aggr-list"      : [ "" ],
            "network"        : [
                {
                    "lif-name"      : "",
                    "role"          : "",
                    "home-node"     : "",
                    "home-port"     : "",
                    "data-protocol" : "",
                    "ip-addr"       : "",
                    "netmask"       : ""
                }
            ],
            "igroups" : [
                {
                    "igroup-name"    : "",
                    "igroup-type"    : "",
                    "os-type"        : ""
                    "initiator-list" : [
                        "",
                        ""
                    ]
                }
            ],
            "volumes" : [
                {
                    "vol-name"             : "",
                    "vol-size-gb"          : 0,
                    "vol-quantity"         : 0,
                    "aggr-list"            : [ "" ],
                    "volume-type"          : "",
                    "security-style"       : "",
                    "snapshot-policy"      : "",
                    "pct-snapshot-reserve" : 0,
                    "luns" : {
                        "lun-name" : "",
                        "lun-quantity" : 0,
                        "os-type"      : "",
                        "space-reservation-enabled" : "",
                        "space-allocation-enabled"  : "",
                        "igroup"                    : [ "" ],
                        "map-to-all"                : true/false
                    }
                }
            ]
        }
    ]    
}
```
