
### Примеры

from its_utils.app_vk import vk

api_without_token = vk.API(v='5.44')
result= api_without_token.groups.getMembers(group_id=1)
{u'count': 342945, u'items': [5, 6, 11, 23, 34, 37, 39, 46, 47, 56, 57, 121, 134, 149, 175, 193, 243......

api_with_token = vk.API(access_token=settings.VK_TOKEN, v='5.44', timeout=30)
result= api_without_token.groups.getMembers(group_id=1)




=========================
vk.com API Python wrapper
=========================

This is a vk.com (the largest Russian social network)
python API wrapper. The goal is to support all API methods (current and future)
that can be accessed from server.

Quickstart
==========

Install
-------

.. code:: bash

    pip install vk

Usage
-----

.. code:: python

    >>> from its_utils.app_vk import vk
    >>> api = vk.API(v=5)
    >>> api.users.get(user_ids=1)
    [{u'first_name': u'\u041f\u0430\u0432\u0435\u043b', u'last_name': u'\u0414\u0443\u0440\u043e\u0432', u'id': 1}]

See https://vk.com/dev/methods for detailed API guide.

More info
=========

`Read full documentation <http://vk.readthedocs.org>`_