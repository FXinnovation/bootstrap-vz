#!/usr/bin/python3
import boto.ec2
import sys
from optparse import OptionParser
parser = OptionParser()
parser.add_option("--aminametag",
                  dest="aminametag",
                  help="Name to tag AMI with")
(options, args) = parser.parse_args()
for region in boto.ec2.regions():
    if region.name == 'cn-north-1' or region.name == 'us-gov-west-1':
        continue
    print("Region: %s" % (region.name))
    ec2 = boto.ec2.connect_to_region(region.name)
    amis = ec2.get_all_images(owners="self",
                              filters={"tag:Name": options.aminametag})
    for ami in amis:
        print (" AMI %s being reset" % (ami.id))
        ec2.reset_image_attribute(ami.id, attribute='launchPermission')
        snapshot_id = ami.block_device_mapping[ami.root_device_name]\
                         .snapshot_id
        print(" -- Snapshot %s being reset" % (snapshot_id))
        ec2.reset_snapshot_attribute(snapshot_id,
                                     attribute='createVolumePermission')
