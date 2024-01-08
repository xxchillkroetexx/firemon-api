# Standard packages
import logging
from typing import Optional

# Local packages
from firemon_api.core.app import App
from firemon_api.core.api import FiremonAPI
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.errors import SecurityManagerError
from firemon_api.core.response import Record, BaseRecord
from firemon_api.core.query import Request, RequestResponse, RequestError

log = logging.getLogger(__name__)


class UsersError(SecurityManagerError):
    pass


class Permission(BaseRecord):
    """A Permission."""

    _ep_name = "permissions"

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)

    def __repr__(self):
        return f"Permission<(id='{self.id}')>"

    def __str__(self):
        return f"{self.id}"


class User(Record):
    """Represents a User in Firemon

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()

    Examples:

        Unlock and Enable all users

        >>> for user in fm.sm.users.all():
        ...   user.enabled = True
        ...   user.locked = False
        ...   user.save()
    """

    _ep_name = "user"
    _is_domain_url = True

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)

    def set_password(self, password: str) -> RequestResponse:
        key = "password"
        data = {"password": password}
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Suppress-Auth-Header": "true",
        }
        req = Request(
            base=self._url,
            key=key,
            headers=headers,
            session=self._session,
        )
        return req.put(data=data)

    def __str__(self):
        return str(self.username)


class Users(Endpoint):
    """Represents the Users

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = "user"
    _is_domain_url = True

    def __init__(self, api: FiremonAPI, app: App, record=User):
        super().__init__(api, app, record=record)

    def _make_filters(self, values):
        # Only a 'search' for a single value. Take all key-values
        # and use the first key's value for search query
        filters = {"search": values[next(iter(values))]}
        filters.update({"includeSystem": True, "includeDisabled": True})
        return filters

    def all(self) -> list[User]:
        """Get all `Record`"""
        filters = {"includeSystem": True, "includeDisabled": True}

        req = Request(
            base=self.url,
            filters=filters,
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]

    def create(self, user_config: dict, system_user: bool = False) -> User:
        """Creates an object on an endpoint.

        Args:
            user_config (dict): a dictionary of all the needed options

        Kwargs:
            system_user (bool): default (False) create user as a system user

        Return:
            (obj): Record
        """

        base_url = None
        if system_user:
            base_url = f"{self.app_url}/{self.__class__.ep_name}"

        req = Request(
            base=base_url if base_url else self.url,
            session=self.api.session,
        ).post(json=user_config)

        if isinstance(req, list):
            return [self._response_loader(i) for i in req]

        return self._response_loader(req)

    def get(self, *args, **kwargs) -> Optional[User]:
        """Get single User

        Args:
            *args (int/str): (optional) id or name to retrieve.
            **kwargs (str): (optional) see filter() for available filters

        Examples:

            Get by ID

            >>> fm.sm.devices.get(1)
            <User(firemon)>

            >>> fm.sm.devices.get("workflow")
            <User(workflow)>
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
            # Attempt to get the 'username'
            user_all = self.all()
            id = args[0]
            user_l = [user for user in user_all if user.username == id]
            if len(user_l) == 1:
                return user_l[0]
            else:
                raise UsersError(f"The requested username: {id} could not be found")
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

    def template(self) -> dict:
        """Create a template of a simple user

        Return:
            dict: dictionary of data to pass to create
        """
        conf = {}
        conf["username"] = None
        conf["firstName"] = None
        conf["lastName"] = None
        conf["email"] = None
        conf["password"] = None
        conf["existingPassword"] = None
        conf["passwordExpired"] = False
        conf["locked"] = False
        conf["expired"] = False
        conf["enabled"] = True
        conf["authType"] = "LOCAL"
        conf["authServerId"] = None  # 0
        return conf


class UserGroup(Record):
    """Represents a UserGroup in Firemon

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()
    """

    _ep_name = "usergroup"
    _is_domain_url = True

    def __init__(self, config: dict, app: App):
        super().__init__(config, app)

    def permission_list(self) -> list[Permission]:
        """List all available permissions in Firemon.

        Return:
            list: list of available permissions.
        """

        key = "permissiondefinition"
        resp = Request(
            base=self._app.domain_url,
            key=key,
            session=self._session,
        ).get()

        perms = []
        for rg in resp:
            # perms.extend(rg['permissions'])
            for p in rg["permissions"]:
                perms.append(Permission(p, self._app))

        return perms

    def permission_show(self) -> list[Permission]:
        key = "permissions"
        resp = Request(
            base=self._url,
            key=key,
            session=self._session,
        ).get()

        perms = []
        for p in resp:
            perms.append(Permission(p, self._app))

        return perms

    def permission_set(self, id: int) -> RequestResponse:
        """Set a permision for UserGroup.

        Args:
            id (int): see permission_list() for id values and meaning
        """
        key = f"permission/{id}"
        resp = Request(
            base=self._url,
            key=key,
            session=self._session,
        ).post()

        return resp

    def permission_unset(self, id: int) -> RequestResponse:
        """Unset a permision for UserGroup.

        Args:
            id (int): see permission_list() for id values and meaning
        """
        key = f"permission/{id}"
        resp = Request(
            base=self._url,
            key=key,
            session=self._session,
        ).delete()

        return resp


class UserGroups(Endpoint):
    """Represents the User Groups

    Args:
        api (obj): FiremonAPI()
        app (obj): App()
        name (str): name of the endpoint

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = "usergroup"
    _is_domain_url = True

    def __init__(self, api: FiremonAPI, app: App, record=UserGroup):
        super().__init__(api, app, record=record)

    def all(self) -> list[UserGroup]:
        """Get all `Record`"""
        filters = {"includeMapping": True}

        req = Request(
            base=self.url,
            filters=filters,
            session=self.api.session,
        )

        return [self._response_loader(i) for i in req.get()]
