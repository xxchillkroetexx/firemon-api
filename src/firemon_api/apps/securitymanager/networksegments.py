# Standard packages
import logging
from typing import List


# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.errors import SecurityManagerError
from firemon_api.core.response import Record, BaseRecord
from firemon_api.core.query import Request


log = logging.getLogger(__name__)


class NetworkSegmentNodeError(SecurityManagerError):
    pass


class NetworkSegmentNode(BaseRecord):
    """Network Segment Node Record.
    NetworkSegmentNode is a reference to a specific device group map node that has a reference to a NetworkSegment.
    A NetworkSegmentNode has a many to one relationship with a NetworkSegment.

    Parameters:
        config (dict): dictionary of things values from json
        app (obj): App()
    """

    _ep_name = "networksegment"
    _is_domain_url = True

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)


class NetworkSegmentNodes(Endpoint):
    """Represents the Network Segment Nodes endpoint

    Parameters:
        api (obj): FiremonAPI()
        app (obj): App()

    Keyword Arguments:
        record (obj): default `Record` object
    """

    ep_name = "networksegmentnode"
    _is_domain_url = True

    def __init__(self, api: FiremonAPI, app: App, record=NetworkSegmentNode):
        super().__init__(api, app, record=record)

    def all(self) -> List[NetworkSegmentNode]:
        device_group_id = 1
        req = Request(
            base=self.domain_url,
            key=f"devicegroup/{device_group_id}/networksegmentnode",
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]

    def get(self, *args, **kwargs):
        node_all = self.all()
        try:
            # Only getting exact matches
            id = args[0]
            node_l = [node for node in node_all if node.nodeId == id]
            if len(node_l) == 1:
                return node_l[0]
            else:
                raise NetworkSegmentNodeError(
                    f"The requested nodeId: {id} could not be found"
                )
        except IndexError:
            id = None

        if not id:
            filter_lookup = self.filter(**kwargs)
            if filter_lookup:
                if len(filter_lookup) > 1:
                    raise ValueError(
                        "get() returned more than one result."
                        "Check the kwarg(s) passed are valid or"
                        "use filter() or all() instead."
                    )
                else:
                    return filter_lookup[0]
            return None

    def filter(self, **kwargs):
        if not kwargs:
            raise ValueError("filter must have kwargs")

        nodes_all = self.all()

        return [node for node in nodes_all if kwargs.items() <= dict(node).items()]

    def get_device_group(self, device_group_id: int) -> List[NetworkSegmentNode]:
        key = f"devicegroup/{device_group_id}/networksegmentnode"
        req = Request(
            base=self.domain_url,
            key=key,
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]

    def get_address(
        self,
        source_address: str | List[str],
        destination_address: str | List[str] = [],
        device_group_id: int = 1,
    ) -> List[NetworkSegmentNode]:
        """Get a list of NetworkSegmentNodes where the given source(s) and destination(s) traffic would most likely start"""
        key = f"devicegroup/{device_group_id}/networksegmentnode/address"
        filters = {}
        filters["address"] = source_address
        if destination_address:
            filters["destination"] = destination_address

        req = Request(
            base=self.domain_url,
            key=key,
            filters=filters,
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]


class NetworkSegmentError(SecurityManagerError):
    pass


class NetworkSegment(Record):
    """Network Segment Record
    NetworkSegment is used on the map and in compliance reporting, but knows nothing of any map.

    Parameters:
        config (dict): dictionary of things values from json
        app (obj): App()
    """

    _ep_name = "networksegment"
    _is_domain_url = True

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)


class NetworkSegments(Endpoint):
    """Represents the Network Segments endpoint

    Parameters:
        api (obj): FiremonAPI()
        app (obj): App()

    Keyword Arguments:
        record (obj): default `Record` object
    """

    ep_name = "networksegment"
    _is_domain_url = True

    def __init__(self, api: FiremonAPI, app: App, record=NetworkSegment):
        super().__init__(api, app, record=record)

    def get(self, *args, **kwargs):
        try:
            key = str(int(args[0]))
            req = Request(
                base=self.url,
                key=key,
                session=self.api.session,
            )

            return self._response_loader(req.get())
        except:
            key = None

        if not key:
            filter_lookup = self.filter(**kwargs)
            if filter_lookup:
                if len(filter_lookup) > 1:
                    raise ValueError(
                        "get() returned more than one result."
                        "Check the kwarg(s) passed are valid or"
                        "use filter() or all() instead."
                    )
                else:
                    return filter_lookup[0]
            return None

    def filter(self, **kwargs):
        if not kwargs:
            raise ValueError("filter must have kwargs")

        seg_all = self.all()

        return [seg for seg in seg_all if kwargs.items() <= dict(seg).items()]
