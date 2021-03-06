"""A run through of base API operations on all supported clouds."""

import os
from contextlib import suppress

import pycloudlib
from pycloudlib.cloud import BaseCloud


cloud_config = """#cloud-config
runcmd:
  - echo 'hello' > /home/ubuntu/example.txt
"""


def exercise_api(client: BaseCloud):
    """Run through supported functions in the base API."""
    try:
        image_id = client.released_image('focal')
    except NotImplementedError:
        image_id = client.daily_image('focal')
    print('focal image id: {}'.format(image_id))
    print('launching instance...')
    instance = client.launch(
        image_id=image_id,
        user_data=cloud_config
    )
    assert repr(instance) == repr(client.get_instance(instance.name))

    print('instance name: {}'.format(instance.name))
    with suppress(NotImplementedError):
        print('instance ip: {}'.format(instance.ip))

    print('starting instance...')
    instance.start()
    print('waiting for cloud-init...')
    instance.execute('cloud-init status --wait --long')
    with suppress(NotImplementedError):
        instance.console_log()
    assert instance.execute('cat /home/ubuntu/example.txt').stdout == 'hello'

    print('restarting instance...')
    instance.execute('sync')  # Prevent's some wtfs :)
    instance.restart()
    assert instance.execute('cat /home/ubuntu/example.txt').stdout == 'hello'

    print('shutting down instance...')
    instance.shutdown()
    print('starting instance...')
    instance.start()
    print(instance.execute('cat /home/ubuntu/example.txt').stdout)
    snapshot_id = None
    with suppress(NotImplementedError):
        print('snapshotting instance...')
        snapshot_id = client.snapshot(instance)
        print('snapshot image id: {}'.format(snapshot_id))
    if snapshot_id:
        assert snapshot_id != image_id
        print('deleting snapshot...')
        client.delete_image(snapshot_id)

    print('deleting instance...')
    instance.delete()


clouds = {
    pycloudlib.Azure: {},
    pycloudlib.EC2: {},
    # pycloudlib.GCE: {
    #     'project': os.environ.get('PROJECT'),
    #     'region': 'us-central1',
    #     'zone': 'a',
    # },
    pycloudlib.OCI: {
        'compartment_id': os.environ.get('COMPARTMENT_ID')
    },
    pycloudlib.KVM: {},
    pycloudlib.LXD: {},
}

if __name__ == '__main__':
    for cloud, kwargs in clouds.items():
        print('Using cloud: {}'.format(cloud.__name__))
        client_api = cloud(tag='base-api-test', **kwargs)
        exercise_api(client_api)
        print()
