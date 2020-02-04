#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
:depends: pysnow

:configuration: This module uses the psnow python module to interact with ServiceNow.

    .. code-block:: text

        https://pysnow.readthedocs.io/en/latest/full_examples/update.html

    This module also requires the existence of several configuration values that
    must be defined in either pillar or the minion configuration.  Expected
    ServiceNow Configuration:


    .. code-block:: yaml

        service_now:
            username: admin
            password: a_secure-password
            instance: dev78478

    Note: ``instance`` is the subdomain portion of your
    ServiceNow Application URI.

'''
from __future__ import absolute_import
import logging
from itertools import islice

LOG = logging.getLogger(__name__)

__virtualname__ = 'snow'

PYSNOW_EXISTS = False
try:
    import pysnow
    PYSNOW_EXISTS = True
except Exception as exc:
    logging.error('pysnow module (https://pysnow.readthedocs.io) not installed')


def __virtual__():
    '''
    Determine whether or not to load this module
    '''
    virtual_return = __virtualname__

    for k in ('username', 'password', 'instance'):
        if not __salt__['config.get']('service_now:{}'.format(k)):
            virtual_return = False
            logging.error('snow module-required config/pillar value service_now:{} not defined'.format(k))  # noqa

    if not PYSNOW_EXISTS:
        virtual_return = False

    return virtual_return


def get_record(tablename, **kwargs):
    """Fetch a record from the given table in ServiceNow

    :tablename: name of the ServiceNow table
    :**kwargs: any query arguments to filter by
    :returns: Response

    >>> salt-call snow.get_record incident number=INC23301

    """
    response = _get_response(tablename, **kwargs)
    return response.one_or_none()


def get_records(tablename, max_results=10, **kwargs):
    """Fetch multiple records from the given table in ServiceNow

    :tablename: name of the ServiceNow table
    :number_results: number of results to return
    :**kwargs: query arguments (e.g. number='INC0010029')
    :returns: Response

    >>> salt-call snow.get_records incident stage=accepted

    """
    table_client = _client_for_table(tablename)
    response = table_client.get(query=kwargs, stream=True)

    records = list(islice(response.all(), max_results))
    return records


def update_record(tablename, query_string, **payload):
    """Update a record. Query should be a string in the format keyname=value
    (e.g. sys_id=really-long-key-from-servicenow)

    >>> salt-call snow.update_record incident number=INC23301 stage=accepted

    """

    query_parts = query_string.split('=')
    query = {query_parts[0]: query_parts[1]}
    record = _get_response(tablename, **query)

    if record:
        return record.update(payload=payload).one()


def _client_for_table(tablename):
    """Get the Service Now Client

    :tablename: the name of the table for which to create resource
    :returns: a pysnow resource object

    """
    service_now_config = __salt__['config.get']('service_now')
    logging.debug('service_now_config: %s', service_now_config)
    c = pysnow.Client(instance=service_now_config['instance'],
                      user=service_now_config['username'],
                      password=service_now_config['password'])

    # Define a resource, here we'll use the incident table API
    return c.resource(api_path='/table/{}'.format(tablename))


def get_incident(incident_number, key='number'):
    """Get an incident by number

    :incident_number: TODO
    :returns: TODO

    """
    incident = _client_for_table('incident')
    ret = incident.get(query={key: incident_number}, stream=True)

    return ret.first()


def _get_response(tablename, **kwargs):
    """Fetch a response from ServiceNow

    :tablename: TODO
    :**kwargs: TODO
    :returns: TODO

    """
    table_client = _client_for_table(tablename)
    response = table_client.get(query=kwargs, stream=True)
    return response
