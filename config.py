__author__ = 'vikalp'

from authomatic.providers import oauth1
import authomatic

CONFIG = {
    'tw':{
        'class_': oauth1.Twitter,
        'consumer_key': 'K98f4OQ5gjTrBhJVqnmcqJd7l',
        'consumer_secret': '2LhUXwDXUSWx6854xuv9L2pxRAm1P2QdwlHsxQ6VDQ4Op5JJ5M',
        'id': authomatic.provider_id()
    },
}
