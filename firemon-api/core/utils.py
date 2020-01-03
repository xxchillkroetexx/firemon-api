"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard packages
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
