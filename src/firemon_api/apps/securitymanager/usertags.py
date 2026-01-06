# Standard packages
import logging
from typing import Literal, Optional
from uuid import UUID

# Local packages
from firemon_api.apps.securitymanager.users import UserGroup
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.errors import SecurityManagerError
from firemon_api.core.response import Record
from firemon_api.core.query import Request, RequestResponse

log = logging.getLogger(__name__)

UserTagType = Literal[
    "CONTROL",
    "NDAPP",
    "NDNATRULE",
    "NDNETWORK",
    "NDPROFILE",
    "NDSCHEDULE",
    "NDSECRULE",
    "NDSERVICE",
    "NDURLMATCHER",
    "NDUSER",
    "REVIEW",
    "TICKET",
]


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
    _is_domain_url = True

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)

    def __str__(self):
        return str(self.name)

    def save(self) -> bool:
        """Saves changes to an existing user tag.
        
        Override the default save() method because the FireMon API
        expects PUT /domain/{domainId}/usertag (without ID in path)
        rather than PUT /domain/{domainId}/usertag/{id}
        
        Returns:
            bool: True if PUT request was successful.
            
        Examples:
            >>> tag = fm.sm.usertags.get(1)
            >>> tag.name = 'Updated Production'
            >>> tag.save()
            True
        """
        if self.id:
            diff = self._diff()
            if diff:
                serialized = self.serialize()
                
                req = Request(
                    base=self._ep_url,
                    session=self._session,
                )
                req.put(json=serialized)
                return True

        return False


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
    _is_domain_url = True

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
                if isinstance(filter_lookup, list) and len(filter_lookup) > 1:
                    raise ValueError(
                        "get() returned more than one result. "
                        "Check that the kwarg(s) passed are valid for this "
                        "endpoint or use filter() or all() instead."
                    )
                else:
                    return filter_lookup[0] if isinstance(filter_lookup, list) else filter_lookup
            return None

    def filter(self, *args, **kwargs):
        """Filter user tags using the Security Manager `q` query parameter.

        Supports:
            - q: raw SM search DSL string, e.g., "name~'Production*'"
            - name: convenience; maps to q="name~'<value>'"
            - name_like: convenience; maps to q="name~'<value>'"
            - only_editable / onlyEditable: boolean to return only tags the user can edit
            - sort: list of sort fields (passed as-is)
            - page: page index (int)
            - page_size / pageSize: page size (int)

        Examples:
            >>> fm.sm.usertags.filter(q="name~'Production*'", only_editable=False, page=0, page_size=10)
            >>> fm.sm.usertags.filter(name='Production')
            >>> fm.sm.usertags.filter(name_like='Production*')
        """
        # Keep a copy for potential fallback to super().filter(...)
        original_kwargs = dict(kwargs)

        # Extract supported params
        q = kwargs.pop("q", None)
        only_editable = kwargs.pop("only_editable", kwargs.pop("onlyEditable", None))
        sort = kwargs.pop("sort", None)
        page = kwargs.pop("page", None)
        page_size = kwargs.pop("page_size", kwargs.pop("pageSize", None))
        name = kwargs.pop("name", None)
        name_like = kwargs.pop("name_like", None)

        # Map convenience params to q
        if q is None and (name is not None or name_like is not None):
            value = name if name is not None else name_like
            # Use 'like' operator (~). Can include wildcard '*' if needed.
            q = f"name~'{value}'"

        # If no 'q' and no recognized SM query params were provided, fall back to the base implementation
        recognized = any(x is not None for x in [q, only_editable, sort, page, page_size, name, name_like])
        if not recognized:
            return super().filter(*args, **original_kwargs)

        filters = {}
        if q is not None:
            filters["q"] = q
        if only_editable is not None:
            filters["onlyEditable"] = only_editable
        if sort is not None:
            filters["sort"] = sort
        if page is not None:
            filters["page"] = page
        if page_size is not None:
            filters["pageSize"] = page_size

        req = Request(
            base=self.url,
            session=self.api.session,
            filters=filters,
        )
        return [self._response_loader(i) for i in req.get()]

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
        sharedUserGroups: Optional[list[UserGroup]] = None,
    ) -> UserTag:
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
        if sharedUserGroups is not None:
            data["sharedUserGroups"] = [{"id": str(group.id)} for group in sharedUserGroups]

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
        conf["sharedUserGroups"] = []
        return conf

    def associate(self, user_tags: list[UserTag], tagType: UserTagType, matchId: UUID) -> bool:
        """Associate a given list of usertags with an object. Not mentioned usertags will be removed.

        Parameters:
            user_tags (list[UserTag]): List of UserTag objects to associate
            tagType (str): Type of object to associate with. One of:
                "CONTROL", "NDAPP", "NDNATRULE", "NDNETWORK", "NDPROFILE",
                "NDSCHEDULE", "NDSECRULE", "NDSERVICE", "NDURLMATCHER",
                "NDUSER", "REVIEW", "TICKET"
            matchId (UUID): UUID of the object to associate with

        Returns:
            bool: True if successful

        Examples:

            >>> tag1 = fm.sm.usertags.get(1)
            >>> tag2 = fm.sm.usertags.get(2)
            >>> fm.sm.usertags.associate([tag1, tag2], 'NDNETWORK', UUID('123e4567-e89b-12d3-a456-426614174000'))
            True
        """
        data = {
            "userTags": [{"id": int(tag.id), "name": str(tag.name), "domainId": int(tag.domainId)} for tag in user_tags],
            "tagType": tagType,
            "matchId": str(matchId),
        }

        req = Request(
            base=f"{self.app_url}/{self.ep_name}/association",
            session=self.session,
        )
        resp = req.put(json=data)
        return resp.ok 
