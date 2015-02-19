#!/usr/bin/python2
import boto.ec2
import time
import sys
from optparse import OptionParser


def get_ami_snapshot_tag_name(ec2, ami):
    attribute = ec2.get_image_attribute(image_id=ami.id,
                                        attribute='blockDeviceMapping')
    if not attribute.attrs['block_device_mapping']:
        return
    for dev in attribute.attrs['block_device_mapping']:
        bdm_snapshot_id = attribute.attrs['block_device_mapping'][dev] \
                                   .snapshot_id
        snaps = ec2.get_all_snapshots(snapshot_ids=bdm_snapshot_id)
        for snap in snaps:
            return snap.tags.get('Name')


def copy_ami(ec2, ami):
    print ("SRC %s:%s, Name=%s" %
           (options.region, ami.id, ami.tags.get('Name')))

    new_ami_ids = []
    for region in regions:
        if region.name == options.region:
            continue
        if region.name == 'cn-north-1':
            continue
        if region.name == 'us-gov-west-1':
            continue

        target_ec2 = boto.ec2.connect_to_region(region.name)
        copy_image_object = target_ec2.copy_image(
            options.region,
            ami.id,
            name=ami.name,
            description=ami.description)
        print ("Copy started to %s (%s)" %
               (region.name, copy_image_object.image_id))

        if copy_image_object.image_id:
            new_ami_ids.append([region.name, copy_image_object.image_id])

    set_tags(
        new_ami_ids,
        ami.tags.get('Name'),
        get_ami_snapshot_tag_name(ec2, ami))
    return new_ami_ids


def set_tags(new_ami_ids, src_ami_tag_name, src_ami_snap_tag_name):
    if options.verbose:
        print("Setting tags on new images")
    for region in new_ami_ids:
        this_reg_ec2 = boto.ec2.connect_to_region(region[0])
        dest_ami = this_reg_ec2.get_all_images(image_ids=(region[1]))
        while dest_ami[0].state != 'available':
            print("Copying to %s (60 seconds sleep)" %
                  (region[0]))
            time.sleep(60)
            dest_ami = this_reg_ec2.get_all_images(image_ids=(region[1]))

        this_reg_ec2.create_tags(
            [region[1]],
            {'Name': src_ami_tag_name})
        if options.share:
            if options.verbose:
                print("Setting launch attribute on AMI %s" % (dest_ami[0].id))
            this_reg_ec2.modify_image_attribute(dest_ami[0].id,
                                                attribute='launchPermission',
                                                operation='add',
                                                groups=["all"])

        if dest_ami[0].root_device_name:
            snapshot_id = dest_ami[0] \
                .block_device_mapping[dest_ami[0].root_device_name] \
                .snapshot_id
            snaps = this_reg_ec2.get_all_snapshots(snapshot_ids=snapshot_id)
            for snap in snaps:
                while snap.status == 'pending':
                    print("Wait 10 sec for snap %s..." % (snapshot_id))
                    time.sleep(10)
            if options.verbose:
                print("Tagging snapshot %s" % (snapshot_id))
            this_reg_ec2.create_tags(snap.id, {'Name': src_ami_snap_tag_name})


parser = OptionParser()
parser.add_option("-r", "--region", dest="region",
                  help="Source region", default="us-east-1")
parser.add_option("--ami", dest="ami",
                  help="Source AMI to copy")
parser.add_option("--aminametag", dest="aminametag",
                  help="Set Name tag on AMI")
parser.add_option("-s", "--share", dest="share",
                  default=False, action='store_true',
                  help="Set AMI as shared")
parser.add_option("-v", "--verbose", dest="verbose",
                  default=False, action='store_true',
                  help="Be verbose")
(options, args) = parser.parse_args()


if (not options.ami):
    print("No AMI ID to copy: fatal")
    sys.exit(1)
regions = boto.ec2.regions()
ec2 = boto.ec2.connect_to_region(options.region)
if (options.aminametag):
    ec2.create_tags(options.ami, {'Name': options.aminametag})
src_ami = ec2.get_all_images(image_ids=options.ami)
copy_ami(ec2, src_ami[0])
