#!/usr/bin/python3
import boto.ec2
import sys
from optparse import OptionParser
parser = OptionParser()
parser.add_option("--aminametag",
                  dest="aminametag",
                  help="Name to tag AMI with")
parser.add_option("--status",
                  dest="status",
                  help="Status to set (eg: Current)")
parser.add_option("-v",
                  "--verbose",
                  dest="verbose",
                  default=False,
                  action="store_true",
                  help="Status to set (eg: Current)")
(options, args) = parser.parse_args()


def find_amis_with_status_tag(ec2, status):
    amis = ec2.get_all_images(owners="self", filters={"tag:Status": status})
    if options.verbose:
        for ami in amis:
            print("%s: %s %s %s %s" % (status,
                                       ami.id,
                                       ami.virtualization_type,
                                       ami.architecture,
                                       ami.root_device_type))
    return amis


def remove_status_tag(ec2, amis, status):
    for ami in amis:
        if options.verbose:
            print("Trying to untag " + ami.id)
        ami.remove_tag("Status", value=status)


def add_status_tag(ec2, amis, status):
    for ami in amis:
        if options.verbose:
            print("Trying to tag " + ami.id)
        ami.add_tag("Status", value=status)


def find_amis_by_name_tag(ec2, name):
    amis = ec2.get_all_images(owners="self", filters={"tag:Name": name})
    if options.verbose:
        print("AMIs with Name " + name)
        for ami in amis:
            print("%s %s %s %s" % (ami.id,
                                   ami.virtualization_type,
                                   ami.architecture,
                                   ami.root_device_type))
    return amis


def find_amis():
    if (not options.aminametag):
        print("Neet to specify aminametag")
        exit(1)

    for region in boto.ec2.regions():
        if options.verbose:
            print("Region: " + region.name)

        if region.name == 'cn-north-1' or region.name == 'us-gov-west-1':
            if options.verbose:
                print("Not dealing with this region")
            continue
        ec2 = boto.ec2.connect_to_region(region.name)
        currently_tagged = find_amis_with_status_tag(ec2, options.status)
        wanted_to_have_tag = find_amis_by_name_tag(ec2, options.aminametag)

        to_add_tag = set()
        to_remove_tag = set()

        for ami in currently_tagged:
            found = 0
            for ami2 in wanted_to_have_tag:
                if ami.id == ami2.id:
                    found = 1
                    break
            if not found:
                to_remove_tag.add(ami)

        for ami in wanted_to_have_tag:
            found = 0
            for ami2 in currently_tagged:
                if ami.id == ami2.id:
                    found = 1
                    break
            if not found:
                to_add_tag.add(ami)

        print("current: " + str(currently_tagged))
        print("wanted: " + str(wanted_to_have_tag))
        print("Remove: " + str(to_remove_tag))
        print("To add: " + str(to_add_tag))

        if to_remove_tag:
            remove_status_tag(ec2, to_remove_tag, options.status)
        if to_add_tag:
            add_status_tag(ec2, to_add_tag, options.status)

find_amis()
