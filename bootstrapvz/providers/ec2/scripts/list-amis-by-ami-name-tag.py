#!/usr/bin/python3
import boto.ec2
import collections
import sys
from optparse import OptionParser
parser = OptionParser()
parser.add_option("--aminametag",
                  dest="aminametag",
                  help="Name to tag AMI with")
(options, args) = parser.parse_args()


def hasher():
    return collections.defaultdict(hasher)


def find_amis():
    ami_table = hasher()
    for region in boto.ec2.regions():
        if region.name == 'cn-north-1' or region.name == 'us-gov-west-1':
            continue
        ec2 = boto.ec2.connect_to_region(region.name)
        amis = ec2.get_all_images(owners="self",
                                  filters={"tag:Name": options.aminametag})
        for ami in amis:
            ami_table[
                region.name][
                ami.virtualization_type][
                ami.architecture][ami.root_device_type] = ami.id
    return ami_table


def key_list(amis):
    key_list = {}
    for region in amis:
        for virt in amis[region]:
            for arch in amis[region][virt]:
                for root in amis[region][virt][arch]:
                    key_list["%s %s %s" % (virt, arch, root)] = 1
    return key_list


def print_amis(amis, key_list):
    sys.stdout.write("|| '''Region''' ")
    for heading in sorted(key_list):
        sys.stdout.write(" || '''" + heading + "'''")
    print(" ||")

    for region in sorted(amis):
        sys.stdout.write("|| %s" % region)
        for virt in sorted(amis[region]):
            for arch in sorted(amis[region][virt]):
                for root in sorted(amis[region][virt][arch]):
                    sys.stdout.write(" || " + amis[region][virt][arch][root])
        print(" ||")

amis = find_amis()
key_list = key_list(amis)
print_amis(amis, key_list)
