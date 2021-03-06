#!/usr/bin/env python3
# This file is part of pycloudlib. See LICENSE file for license information.
"""Basic examples of various lifecycle with a LXD instance."""

import logging

import pycloudlib

RELEASE = 'bionic'


def snapshot_instance():
    """Demonstrate snapshot functionality.

    This shows the lifecycle of booting an instance and cleaning it
    before creating a snapshot.

    Next, both create the snapshot and immediately restore the original
    instance to the snapshot level.

    Finally, launch another instance from the snapshot of the instance.

    """
    lxd = pycloudlib.LXD('example-snapshot')
    inst = lxd.launch('pycloudlib-snapshot-base', RELEASE)

    snapshot_name = 'snapshot'
    inst.snapshot(snapshot_name)
    inst.restore(snapshot_name)

    child = lxd.clone('%s/%s' % (inst.name, snapshot_name),
                      'pycloudlib-snapshot-child')

    child.delete()
    inst.delete_snapshot(snapshot_name)
    inst.delete(wait=False)


def modify_instance():
    """Demonstrate how to modify and interact with an instance.

    The inits an instance and before starting it, edits the the
    container configuration.

    Once started the instance demonstrates some interactions with the
    instance.
    """
    lxd = pycloudlib.LXD('example-modify')

    inst = lxd.init('pycloudlib-modify-inst', RELEASE)
    inst.edit('limits.memory', '3GB')
    inst.start()

    inst.execute('uptime > /tmp/uptime')
    inst.pull_file('/tmp/uptime', '/tmp/pulled_file')
    inst.push_file('/tmp/pulled_file', '/tmp/uptime_2')
    inst.execute('cat /tmp/uptime_2')

    inst.delete(wait=False)


def launch_multiple():
    """Launch multiple instances.

    How to quickly launch multiple instances with LXD. This prevents
    waiting for the instance to start each time. Note that the
    wait_for_delete method is not used, as LXD does not do any waiting.
    """
    lxd = pycloudlib.LXD('example-multiple')

    instances = []
    for num in range(3):
        inst = lxd.launch('pycloudlib-%s' % num, RELEASE, wait=False)
        instances.append(inst)

    for instance in instances:
        instance.wait()

    for instance in instances:
        instance.delete()


def launch_options():
    """Demonstrate various launching scenarios.

    First up is launching with a different profile, in this case with
    two profiles.

    Next, is launching an ephemeral instance with a different image
    remote server.

    Then, an instance with custom network, storage, and type settings.
    This is an example of booting an instance without cloud-init so
    wait is set to False.

    Finally, an instance with custom configurations options.
    """
    lxd = pycloudlib.LXD('example-launch')

    lxd.launch(
        'pycloudlib-kvm', RELEASE, profile_list=['default', 'kvm']
    )
    lxd.delete_instance('pycloudlib-kvm')

    lxd.launch(
        'pycloudlib-ephemeral', 'ubuntu:%s' % RELEASE, ephemeral=True
    )
    lxd.delete_instance('pycloudlib-ephemeral')

    lxd.launch(
        'pycloudlib-custom-hw', 'images:ubuntu/xenial', network='lxdbr0',
        storage='default', inst_type='t2.micro', wait=False
    )
    lxd.delete_instance('pycloudlib-custom-hw')

    lxd.launch(
        'pycloudlib-privileged', RELEASE,
        config_dict={
            'security.nesting': 'true',
            'security.privileged': 'true'
        }
    )
    lxd.delete_instance('pycloudlib-privileged')


def basic_lifecycle():
    """Demonstrate basic set of lifecycle operations with LXD."""
    lxd = pycloudlib.LXD('example-basic')
    name = 'pycloudlib-daily'
    inst = lxd.launch(name, RELEASE)
    inst.console_log()

    result = inst.execute('uptime')
    print(result)
    print(result.return_code)
    print(result.ok)
    print(result.failed)
    print(bool(result))

    inst.shutdown()
    inst.start()
    inst.restart()

    # Custom attributes
    print(inst.ephemeral)
    print(inst.state)

    inst = lxd.get_instance(name)
    inst.delete()


def demo():
    """Show examples of using the LXD library."""
    basic_lifecycle()
    launch_options()
    launch_multiple()
    modify_instance()
    snapshot_instance()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    demo()
