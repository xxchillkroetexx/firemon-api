"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard packages
import logging

# Local packages
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record, JsonField
from firemon_api.core.query import Request, url_param_builder, RequestError
from firemon_api.core.utils import _build_dict

log = logging.getLogger(__name__)


class Revision(Record):
    """Revision `Record`
    'ndrevisions' and 'normalization'.

    (change configuration &/or normalization state)

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()

    Examples:
        >>> rev = fm.sm.revisions.filter(latest=True, deviceName='vSRX-2')[0]
        >>> zip = rev.export()
        >>> with open('export.zip', 'wb') as f:
        ...   f.write(zip)
        ...
        36915
        >>> zip = rev.export(meta=False)
        >>> rev.delete()
        True
    """

    _ep_name = "rev"

    def __init__(self, config, app):
        super().__init__(config, app)

        self._domain_id = config["domainId"]
        self._device_id = config["deviceId"]
        self.files = self._files_load()

    def save(self):
        raise NotImplementedError("Writes are not supported.")

    def update(self):
        raise NotImplementedError("Writes are not supported.")

    def delete(self):
        """Deletes an existing object.
        :returns: True if DELETE operation was successful.
        :example:
        >>> dev = fm.sm.devices.get(name='vsrx2')
        >>> rev = dev.revisions.get(224)
        >>> rev.delete()
        True
        >>>
        """
        req = Request(
            base=self._app_url,
            key=f"domain/{self.domainId}/device/{self.deviceId}/rev/{self.id}",
            session=self._session,
        )
        return True if req.delete() else False

    def export(self, meta: bool = True):
        """Export a zip file contain the config data.

        Support files include all NORMALIZED data and other meta data.
        Raw configs include only those files as found by Firemon
        during a retrieval.

        Kwargs:
            meta (bool): Include metadata and NORMALIZED config files

        Return:
            bytes: zip file
        """
        if meta:
            key = "export"
        else:
            key = "export/config"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        return req.get_content()

    def nd_get(self, sections: list = []):
        """Get normalized data as a fully parsed object

        Retrieve all the revision data in a single payload.

        Kwargs:
            sections (list): different sections of Normalized Data to retrieve
                "empty" (default): every section
                "app":
                "... etc": all the different things

        """
        key = f"nd/all"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        if sections:
            filters = {"types": ",".join(sections)}
            req.filters = filters
        return NormalizedData(req.get(), self._app)

    def _files_load(self):
        """Get the file descriptors attached to Revision"""
        key = "nd/file"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        return [RevFile(i, self._app, self.id) for i in req.get()]

    def nd_problem(self):
        """Get problems with revision"""
        key = "nd/problem"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        return req.get()


class Revisions(Endpoint):
    """Revisions Endpoint.
    Combining 'ndrevisions' and 'normalization'.
    Filtering is what it is. It is a mixture of revID,
    static domain requirements and device_id, or searching by a subset
    of our internal SIQL (but you cannot search by name or anything in SIQL).

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
        device_id (int): Device id

    Examples:
        >>> rev = fm.sm.revisions.get(34)
        >>> rev = fm.sm.revisions.filter(latest=True, deviceName='vSRX-2')[0]
    """

    ep_name = "rev"

    def __init__(self, api, app, record=Revision, device_id: int = None):
        super().__init__(api, app, record=Revision)
        self._device_id = device_id

    def all(self):
        """Get all `Record`"""
        if self._device_id:
            all_key = f"device/{self._device_id}/{self.__class__.ep_name}"
        else:
            all_key = f"{self.__class__.ep_name}"

        req = Request(
            base=self.domain_url,
            key=all_key,
            session=self.session,
        )

        revs = [self._response_loader(i) for i in req.get()]
        return sorted(revs, key=lambda x: x.id, reverse=True)

    def filter(self, *args, **kwargs):
        """Retrieve a filterd list of Revisions.

        I have no idea how our /filter endpoint works. Some SIQL but
        I cannot find any decent documentation.

        Args:
            **kwargs: key value pairs in a device pack dictionary

        Return:
            list: a list of Revision(object)

        Examples:

        >>> fm.sm.dp.filter(latest=True)
        """

        rev_all = self.all()
        if not kwargs:
            raise ValueError("filter must have kwargs")

        revs = [rev for rev in rev_all if kwargs.items() <= dict(rev).items()]
        return sorted(revs, key=lambda x: x.id, reverse=True)

    @property
    def device_id(self):
        return self._device_id


class RevFile(Record):
    """A Revision File"""

    _ep_name = "rev"

    def __init__(self, config, app, rev_id):
        self.rev_id = rev_id
        super().__init__(config, app)

    def _url_create(self):
        """General self.url create"""
        url = f"{self._ep_url}/{self.rev_id}/nd/file/{self._config['id']}"
        return url

    def save(self):
        raise NotImplementedError("Writes are not supported for this Record.")

    def update(self):
        raise NotImplementedError("Writes are not supported for this Record.")

    def delete(self):
        raise NotImplementedError("Writes are not supported for this Record.")

    def get(self):
        """Get the raw file

        Return:
            bytes: the bytes that make up the file
        """
        req = Request(
            base=self._url,
            session=self._session,
        )
        return req.get_content()

    def __repr__(self):
        return f"RevFile<(name='{self.name}')>"

    def __str__(self):
        return f"{self.name}"


class NormalizedData(Record):
    """A NORMALIZED Revision. All the things."""

    _ep_name = "rev"

    def __init__(self, config, app):
        super().__init__(config, app)

    def save(self):
        raise NotImplementedError("Writes are not supported for this Record.")

    def update(self):
        raise NotImplementedError("Writes are not supported for this Record.")

    def delete(self):
        raise NotImplementedError("Writes are not supported for this Record.")

    def _url_create(self):
        """General self.url create"""
        url = f"{self._ep_url}/{self._config['revisionId']}"
        return url

    def __str__(self):
        return str(self.revisionId)
