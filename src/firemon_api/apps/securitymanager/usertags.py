# Standard packages
import logging
from typing import Optional

# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.errors import SecurityManagerError
from firemon_api.core.response import Record
from firemon_api.core.query import Request, RequestResponse

log = logging.getLogger(__name__)


class UserTagsError(SecurityManagerError):
    pass


class UserTag(Record):
    """Represents a UserTag in Firemon

    Parameters:
        config (dict): dictionary of things values from json
        app (obj): App()

    Examples:

        >>> tag = fm.sm.usertags.get(1)
        >>> tag.name
        'Production'
        >>> tag.color
        '#FF0000'
    """

    _ep_name = "usertag"
    _is_domain_url = False

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)

    def __str__(self):
        return str(self.name)


class UserTags(Endpoint):
    """Represents the UserTags

    Parameters:
        api (obj): FiremonAPI()
        app (obj): App()

    Keyword Arguments:
        record (obj): default `Record` object

    Examples:

        >>> tags = fm.sm.usertags.all()
        >>> tag = fm.sm.usertags.get(1)
        >>> tag = fm.sm.usertags.get(name='Production')
    """

    ep_name = "usertag"
    _is_domain_url = False

    def __init__(self, api: FiremonAPI, app: App, record=UserTag):
        super().__init__(api, app, record=record)

    def get(self, *args, **kwargs) -> Optional[UserTag]:
        """Get single UserTag

        Parameters:
            *args (int/str): (optional) id or name to retrieve.
            **kwargs (str): (optional) see filter() for available filters

        Returns:
            UserTag

        Examples:

            Get by ID

            >>> fm.sm.usertags.get(1)
            <UserTag(Production)>

            Get by name. Case sensitive.

            >>> fm.sm.usertags.get(name='Production')
            <UserTag(Production)>
        """

        try:
            key = str(int(args[0]))
            req = Request(
                base=self.url,
                key=key,
                session=self.api.session,
            )
            return self._response_loader(req.get())
        except ValueError:
            # Not an integer, treat as filter
            pass
        except IndexError:
            key = None

        if not key:
            if kwargs:
                filter_lookup = self.filter(**kwargs)
            else:
                filter_lookup = self.filter(*args)
            if filter_lookup:
                if len(filter_lookup) > 1:
                    raise ValueError(
                        "get() returned more than one result. "
                        "Check that the kwarg(s) passed are valid for this "
                        "endpoint or use filter() or all() instead."
                    )
                else:
                    return filter_lookup[0]
            return None

    def create(self, name: str, description: Optional[str] = None, 
               color: Optional[str] = None) -> UserTag:
        """Create a new usertag

        Parameters:
            name (str): Name of the usertag

        Keyword Arguments:
            description (str): Optional description
            color (str): Optional color code (hex format, e.g., '#FF0000')

        Returns:
            UserTag: newly created usertag

        Examples:

            >>> tag = fm.sm.usertags.create('Production', description='Production systems', color='#FF0000')
            <UserTag(Production)>
        """
        data = {"name": name}
        if description is not None:
            data["description"] = description
        if color is not None:
            data["color"] = color

        req = Request(
            base=self.url,
            session=self.api.session,
        ).post(json=data)

        return self._response_loader(req)

    def template(self) -> dict:
        """Create a template for a usertag

        Returns:
            dict: dictionary of data to pass to create

        Examples:

            >>> config = fm.sm.usertags.template()
            >>> config['name'] = 'Development'
            >>> config['description'] = 'Dev environment'
            >>> config['color'] = '#00FF00'
            >>> tag = fm.sm.usertags.create(**config)
        """
        conf = {}
        conf["name"] = None
        conf["description"] = None
        conf["color"] = None
        return conf
