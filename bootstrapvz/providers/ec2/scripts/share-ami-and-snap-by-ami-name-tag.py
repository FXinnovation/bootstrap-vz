#!/usr/bin/python3
import boto.ec2
import sys
from optparse import OptionParser
parser = OptionParser()
parser.add_option("--aminametag",
                  dest="aminametag",
                  help="Name to tag AMI with")
parser.add_option("-v", "--verbose", dest="verbose",
                  default=False, action='store_true',
                  help="Be verbose")

(options, args) = parser.parse_args()
for region in boto.ec2.regions():
    if region.name == 'cn-north-1' or region.name == 'us-gov-west-1':
        continue
    print("Region: %s" % (region.name))
    ec2 = boto.ec2.connect_to_region(region.name)
    amis = ec2.get_all_images(owners="self",
                              filters={"tag:Name": options.aminametag})
    for ami in amis:
        print(" AMI %s being shared" % (ami.id))
        ec2.modify_image_attribute(ami.id,
                                   attribute='launchPermission',
                                   operation='add',
                                   groups=["all"])
        if ami.root_device_name:
            snapshot_id = ami.block_device_mapping[ami.root_device_name]\
                             .snapshot_id
            if options.verbose:
                print(" Snapshot %s being shared" % (snapshot_id))
            ec2.modify_snapshot_attribute(snapshot_id,
                                          attribute='createVolumePermission',
                                          operation='add',
                                          groups=["all"])
