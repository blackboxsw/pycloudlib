# This file is part of pycloudlib. See LICENSE file for license information.
"""GCE Cloud type.

This is an initial implimentation of the GCE class. It enables
authentication into the cloud, finding an image, and launching an
instance. It however, does not allow any further actions from occuring.
"""

import logging
import time

import googleapiclient.discovery

from pycloudlib.cloud import BaseCloud
from pycloudlib.key import KeyPair
from pycloudlib.streams import Streams

logging.getLogger('googleapiclient.discovery').setLevel(logging.WARNING)


class GCE(BaseCloud):
    """GCE Cloud Class."""

    def __init__(
        self, tag, timestamp_suffix=True, project=None, region=None, zone=None
    ):
        """Initialize the connection to GCE.

        Args:
            tag: string used to name and tag resources with
            timestamp_suffix: bool set True to append a timestamp suffix to the
                tag
            project:
            region:
            zone:
        """
        super().__init__(tag, timestamp_suffix)
        self._log.debug('logging into GCE')

        # disable cache_discovery due to:
        # https://github.com/google/google-api-python-client/issues/299
        self.compute = googleapiclient.discovery.build(
            'compute', 'v1', cache_discovery=False
        )
        self.project = project
        self.region = region
        self.zone = '%s-%s' % (region, zone)

    def released_image(self, release):
        """ID of the latest released image for a particular release.

        Args:
            release: The release to look for

        Returns:
            A single string with the latest released image ID for the
            specified release.

        """
        raise NotImplementedError

    def daily_image(self, release, arch='amd64'):
        """Find the id of the latest image for a particular release.

        Args:
            release: string, Ubuntu release to look for
            arch: string, architecture to use

        Returns:
            string, path to latest daily image

        """
        self._log.debug('finding daily Ubuntu image for %s', release)
        images = self._image_list(release, arch)

        try:
            image_id = images[0]['id']
        except IndexError:
            Exception('No images found')

        return 'projects/ubuntu-os-cloud-devel/global/images/%s' % image_id

    def image_serial(self, image_id):
        """Find the image serial of the latest daily image for a particular release.

        Args:
            image_id: string, Ubuntu image id

        Returns:
            string, serial of latest image

        """
        raise NotImplementedError

    def delete_image(self, image_id):
        """Delete an image.

        Args:
            image_id: string, id of the image to delete
        """
        raise NotImplementedError

    def get_instance(self, instance_id):
        """Get an instance by id.

        Args:
            instance_id:

        Returns:
            An instance object to use to manipulate the instance further.

        """
        raise NotImplementedError

    def launch(self, image_id, instance_type='n1-standard-1', user_data=None,
               wait=True, **kwargs):
        """Launch instance on GCE and print the IP address.

        Args:
            image_id: string, image ID for instance to use
            instance_type: string, instance type to launch
            user_data: string, user-data to pass to instance
            wait: boolean, wait for instance to come up
            kwargs: other named arguments to add to instance JSON

        """
        if user_data:
            self._log.warning('GCE platform does not support user-data')

        config = {
            'name': self.tag,
            'machineType': 'zones/%s/machineTypes/%s' % (
                self.zone, instance_type
            ),
            'disks': [{
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': image_id,
                }
            }],
            'networkInterfaces': [{
                'network': 'global/networks/default',
                'accessConfigs': [
                    {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
                ]
            }],
            "metadata": {
                "items": [{
                    "key": "ssh-keys",
                    "value": "admin:%s" % self.key_pair.public_key_content,
                }]
            },
        }

        operation = self.compute.instances().insert(
            project=self.project,
            zone=self.zone,
            body=config
        ).execute()

        self._wait_for_operation(operation)

        result = self.compute.instances().get(
            project=self.project,
            zone=self.zone,
            instance=self.tag
        ).execute()

        self._log.info(
            result['networkInterfaces'][0]['accessConfigs'][0]['natIP']
        )

    def snapshot(self, instance, clean=True):
        """Snapshot an instance and generate an image from it.

        Args:
            instance: Instance to snapshot
            clean: run instance clean method before taking snapshot

        Returns:
            An image object

        """
        raise NotImplementedError

    def use_key(self, public_key_path, private_key_path=None, name=None):
        """Use an existing already uploaded key.

        Args:
            public_key_path: path to the public key to upload
            private_key_path: path to the private key to upload
            name: name to reference key by
        """
        self._log.debug('using SSH key from %s', public_key_path)
        self.key_pair = KeyPair(public_key_path, private_key_path, name)

    def _image_list(self, release, arch='amd64'):
        """Find list of images with a filter.

        Args:
            release: string, Ubuntu release to look for
            arch: string, architecture to use

        Returns:
            list of dictionaries of images

        """
        filters = [
            'arch=%s' % arch,
            'endpoint=%s' % 'https://www.googleapis.com',
            'region=%s' % self.region,
            'release=%s' % release,
            'virt=kvm'
        ]

        stream = Streams(
            mirror_url='https://cloud-images.ubuntu.com/daily',
            keyring_path='/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg'
        )

        return stream.query(filters)

    def _wait_for_operation(self, operation):
        """TODO."""
        while True:
            time.sleep(5)
            result = self.compute.zoneOperations().get(
                project=self.project,
                zone=self.zone,
                operation=operation['name']
            ).execute()

            if result['status'] == 'DONE':
                if 'error' in result:
                    raise Exception(result['error'])
                return result
