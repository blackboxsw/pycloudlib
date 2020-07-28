# This file is part of pycloudlib. See LICENSE file for license information.
"""EC2 Util Functions."""

import base64
import datetime

import boto3
import botocore


def _tag_resource(resource, tag_value=None):
    """Tag a resource with the specified tag.

    This makes finding and deleting resources specific to this testing
    much easier to find.

    Args:
        resource: resource to tag
        tag_value: string, what to tag the item with
    """
    if not tag_value:
        tag_value = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    tag = {
        'Key': 'Name',
        'Value': tag_value
    }
    resource.create_tags(Tags=[tag])


def _decode_console_output_as_bytes(parsed, **kwargs):
    """Provide console output as bytes in OutputBytes.

    For this to be useful, the session has to have had the
    decode_console_output handler unregistered already.

    https://github.com/boto/botocore/issues/1351

    Args:
        parsed: the raw console output
    """
    if 'Output' not in parsed:
        return
    orig = parsed['Output']
    botocore.handlers.decode_console_output(parsed, **kwargs)
    parsed['OutputBytes'] = base64.b64decode(orig)


def _get_session(access_key_id, secret_access_key, region, ssl_validate=True):
    """Get EC2 session.

    Args:
        access_key_id: user's access key ID
        secret_access_key: user's secret access key
        region: region to login to
        ssl_validate: whether or not to validate SSL endpoints

    Returns:
        boto3 session object

    """
    mysess = botocore.session.get_session()
    mysess.unregister('after-call.ec2.GetConsoleOutput',
                      botocore.handlers.decode_console_output)
    mysess.register('after-call.ec2.GetConsoleOutput',
                    _decode_console_output_as_bytes)
    return boto3.Session(
        botocore_session=mysess,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        validate=False,
        region_name=region,
    )
