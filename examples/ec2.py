#!/usr/bin/env python3
# This file is part of pycloudlib. See LICENSE file for license information.
"""Basic examples of various lifecycle with an EC2 instance."""

import logging

import pycloudlib


def hot_add(ec2, daily):
    """Hot add to an instance.

    Give an example of hot adding a pair of network interfaces and a
    couple storage volumes of various sizes.
    """
    instance = ec2.launch(daily, instance_type='m4.xlarge')

    instance.add_network_interface()
    instance.add_network_interface()

    instance.add_volume(size=9)
    instance.add_volume(size=10, drive_type='gp2')

    instance.delete()


def launch_multiple(ec2, daily):
    """Launch multiple instances.

    How to quickly launch multiple instances with EC2. This prevents
    waiting for the instance to start each time.
    """
    instances = []
    for _ in range(3):
        instances.append(ec2.launch(daily, wait=False))

    for instance in instances:
        instance.wait()

    for instance in instances:
        instance.delete(wait=False)

    for instance in instances:
        instance.wait_for_delete()


def snapshot(ec2, daily):
    """Create a snapshot from a customized image and launch it."""
    instance = ec2.launch(daily)
    instance.execute('touch custom_config_file')

    image = ec2.snapshot(instance)
    new_instance = ec2.launch(image)
    new_instance.execute('ls')

    new_instance.delete()
    ec2.delete_image(image)
    instance.delete()


def custom_vpc(ec2, daily):
    """Launch instances using a custom VPC."""
    vpc = ec2.get_or_create_vpc(name='test-vpc')
    ec2.launch(daily, vpc=vpc)

    # vpc.delete will also delete any associated instances in that VPC
    vpc.delete()


def launch_basic(ec2, daily):
    """Show bassic functionality on instances.

    Simple launching of an instance, run a command, and delete.
    """
    instance = ec2.launch(daily)
    instance.console_log()
    instance.execute('ip a')

    instance.shutdown()
    instance.start()
    instance.restart()

    # Various Attributes
    print(instance.ip)
    print(instance.id)
    print(instance.image_id)
    print(instance.availability_zone)

    instance.delete()


def demo():
    """Show example of using the EC2 library.

    Connects to EC2 and finds the latest daily image. Then runs
    through a number of examples.
    """
    ec2 = pycloudlib.EC2(tag='examples')
    daily = ec2.daily_image(release='bionic')

    launch_basic(ec2, daily)
    custom_vpc(ec2, daily)
    snapshot(ec2, daily)
    launch_multiple(ec2, daily)
    hot_add(ec2, daily)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    demo()
