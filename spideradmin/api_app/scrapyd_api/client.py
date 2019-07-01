from __future__ import unicode_literals

import logging

from requests import Session
from requests.exceptions import ConnectionError


class Client(Session):
    """
    The client is a thin wrapper around the requests Session class which
    allows us to wrap the response handler so that we can handle it in a
    Scrapyd-specific way.
    """

    def request(self, *args, **kwargs):
        try:
            kwargs["timeout"] = 10
            response = super(Client, self).request(*args, **kwargs)
            data = response.json()
        except Exception as e:
            logging.error("### Error: {}".format(e))
            data = {"status": "error"}

        return data
