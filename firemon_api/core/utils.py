"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard packages
#import functools
#from distutils.version import StrictVersion
from typing import Generator



def _find_dicts_with_key(key: str, dictionary: dict) -> Generator[dict, None, None]:
    """
    Find all dictionaries that contain a key.

    Args:
        key (str): the key value to find.
        dictionary (dict): the dictionary hiding the keys to find.

    Yield:
        dict: the dictionary containing the key
    """
    if isinstance(dictionary, dict):
        if key in dictionary.keys():
            yield dictionary
        for k, v in dictionary.items():
            if isinstance(v, dict) or isinstance(v, list):
                for response in _find_dicts_with_key(key, v):
                    yield response
    elif isinstance(dictionary, list):
        for item in dictionary:
            if isinstance(item, dict) or isinstance(item, list):
                for response in _find_dicts_with_key(key, item):
                    yield response

def _build_dict(seq: list, key: str) -> dict:
    """ Build a dictionary from a list(of dictionaries) against a given key
    https://stackoverflow.com/questions/4391697/find-the-index-of-a-dict-within-a-list-by-matching-the-dicts-value

    Args:
        seq (list): a list of dictionaries
        key (str): the key value that is found in the dictionaries

    Retrun:
        dict: a dictionary with the index value of the list, key value, and the stuff.
    """
    return dict((d[key], dict(d, index=index)) for (index, d) in enumerate(seq))

class Hashabledict(dict):
    def __hash__(self):
        return hash(frozenset(self))

#class ApiVersionError(Exception):
#    """Basic Exception"""
#    def __init__(self, message):
#        super(ApiVersionError, self).__init__(message)

#def version_check(min_ver=None, max_ver=None):
#    """Decorator maker for _version_check
#    Not all API calls are available for all versions.
#
#    Note: Not sure that we will ever use this decorator and
#        instead rely on the call failing from `Request`
#
#    Kwargs:
#        min_ver (str): minimum version
#        max_ver (str): maximum version
#    """
#    def _version_check(func):
#        @functools.wraps(func)
#        def wrapped(self, *args, **kwargs):
#            ver = self.api.version
#            if not min_ver and not max_ver:
#                return func(self, *args, **kwargs)
#            if min_ver and max_ver:
#                if StrictVersion(min_ver) > StrictVersion(max_ver):
#                    raise ApiVersionError('Programmer messed up decorator')
#                if StrictVersion(min_ver) <= StrictVersion(ver) <= StrictVersion(max_ver):
#                    return func(self, *args, **kwargs)
#                else:
#                    raise ApiVersionError('Api version mismatch: '
#                                        'Outside min-max version boundaries')
#            elif min_ver:
#                if StrictVersion(min_ver) <= StrictVersion(ver):
#                    return func(self, *args, **kwargs)
#                else:
#                    raise ApiVersionError('Api version mismatch: '
#                                        'Version is lower than min API version')
#            elif max_ver:
#                if StrictVersion(ver) <= StrictVersion(max_ver):
#                    return func(self, *args, **kwargs)
#                else:
#                    raise ApiVersionError('Api version mismatch: '
#                                        'Version is higher than max API version')
#            else:
#                raise ApiVersionError('Programmer messed up I suspect')
#        return wrapped
#    return _version_check
