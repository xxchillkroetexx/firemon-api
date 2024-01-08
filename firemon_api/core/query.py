# Standard packages
import concurrent.futures as cf

from json.decoder import JSONDecodeError
import logging
from typing import Union, Optional
from urllib.parse import urlencode


# third-party
from requests import Session
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from firemon_api.core.errors import FiremonApiError

log = logging.getLogger(__name__)

RequestResponse = Union[bool, dict, str, bytes]


def url_param_builder(param_dict: dict) -> str:
    """Builds url parameters
    Creates URL paramters (e.g. '.../?xyz=r21&abc=123') from a dict passed in param_dict
    """
    return f"?{urlencode(param_dict)}"


def calc_pages(pageSize: int, total: int) -> int:
    """Calculate number of pages required for full results set."""
    return int(total / pageSize) + (pageSize % total > 0)


class RequestError(FiremonApiError):
    """Basic Request Exception
    More detailed exception that returns the original requests object
    for inspection. Along with some attributes with specific details
    from the requests object. If return is json we decode and add it
    to the message.
    """

    def __init__(self, message):
        req = message

        if req.status_code == 404:
            message = f"The requested url: {req.url} could not be found."
        else:
            try:
                message = f"The request failed with code {req.status_code} {req.reason}: {req.json()}"
            except ValueError:
                message = (
                    f"The request failed with code {req.status_code} {req.reason} but more specific "
                    "details were not returned in json."
                )

        super(RequestError, self).__init__(message)
        self.req = req
        self.request_body = req.request.body
        self.base = req.url
        self.error = req.text


class Request(object):
    """Creates requests to the FireMon API
    Responsible for building the url and making the HTTPS requests to FireMon's API

    Args:
        base (str) Base URL
        session (`Session`): requests

    Kwargs:
        filters (dict, optional): contains key/value pairs that correlate to the filters a given endpoint accepts.
        key (str, optional): append to base to make up full url
        headers (dict, optional): specific headers to over ride session headers
        cookies (dict, optional):
        trailing_slash (bool): Ensure a trailing slash for `self.url`retry_count (int): number of times to retry request call for any error except `RequestError`. Helps with flakey connections.

    """

    def __init__(
        self,
        base: str,
        session: Session,
        filters: Optional[dict] = None,
        key: Optional[str] = None,
        url: Optional[str] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
        trailing_slash: bool = False,
    ):
        self.base = self.normalize_url(base, trailing_slash=trailing_slash)
        self.session = session
        self.filters = filters
        self.verify = session.verify
        self.key = self.normalize_key(key) if key else None
        self.url = self.base if not key else f"{self.base}/{key}"
        self.headers = headers
        self.cookies = cookies

    def normalize_url(self, url: str, trailing_slash=False) -> str:
        if url[-1] == "/":
            return url.strip("/")
        if trailing_slash:
            return f"{url}/"
        return url

    def normalize_key(self, key: str) -> str:
        if key[0] == "/":
            return key.lstrip("/")
        return key

    # Retry using tenacity
    @retry(
        # retry=retry_if_exception_type(ConnectionError),
        retry=retry_if_not_exception_type(RequestError),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(5),
        before_sleep=before_sleep_log(log, logging.INFO),
        reraise=True,
    )
    def _make_call(
        self,
        verb: str = "get",
        url_override: Optional[str] = None,
        add_params: Optional[dict] = None,
        json: Optional[dict] = None,
        data: Optional[dict] = None,
        files: list = None,
    ) -> RequestResponse:
        if self.headers:
            headers = self.headers
        else:
            if verb in ("post") and files:
                headers = {"Content-Type": "multipart/form-data"}
            elif verb in ("post", "put"):
                headers = {"Content-Type": "application/json;"}
            else:
                headers = {"accept": "application/json;"}

        params = {}
        if not url_override:
            if self.filters:
                params = self.filters
            if add_params:
                params.update(add_params)

        if params:
            log.info(
                f"{verb.upper()}: {url_override or f'{self.url}?{urlencode(params, doseq=True)}'}"
            )
        else:
            log.info(f"{verb.upper()}: {url_override or f'{self.url}'}")

        if json:
            log.info(f"Json: {json}")
        if data:
            log.info(f"Data: {data}")
        if files:
            log.info("Files present")
            for file in files:
                log.debug(f"File : {file}")

        req = getattr(self.session, verb)(
            url_override or self.url,
            headers=headers,
            params=params,
            json=json,
            data=data,
            files=files,
            verify=self.verify,
            cookies=self.cookies,
        )

        log.debug(f"Sent HEADERS {req.request.headers}")  # sent headers
        log.debug(f"Ret. HEADERS {req.headers}")  # returned headers
        if verb == "delete":
            if req.ok:
                return True
            else:
                raise RequestError(req)
        elif req.ok:
            try:
                return req.json()
            except JSONDecodeError:
                # Assuming an empty body or data download
                if req.content:
                    return req.content
                else:
                    return True
        else:
            raise RequestError(req)

    def concurrent_get(self, ret: dict, page_size: int, page_range: list) -> None:
        futures_to_results = []
        with cf.ThreadPoolExecutor(max_workers=4) as pool:
            for page in page_range:
                new_params = {"page": page, "pageSize": page_size}
                futures_to_results.append(
                    pool.submit(self._make_call, add_params=new_params)
                )

            for future in cf.as_completed(futures_to_results):
                result = future.result()
                ret.extend(result["results"])

    def get(self, add_params=None) -> RequestResponse:
        """Makes a GET request.
        Makes a GET request to FireMon API, and automatically recurses
        any paginated results.

        Raises:
            RequestError: if req.ok returns false.

        Returns:
            dict: data from the endpoint.
        """
        if add_params is None:
            # Hopefully this will cut down on queries without breaking things
            add_params = {"pageSize": 100}
        req = self._make_call(add_params=add_params)
        if isinstance(req, dict) and req.get("results") is not None:
            ret = req["results"]
            if req.get("total"):
                # page_size = len(req["results"])
                page_size = req["pageSize"]
                pages = calc_pages(page_size, req["total"])
                # page_offsets = [
                #    increment * page_size for increment in range(1, pages)
                # ]
                page_range = range(1, pages)
                if pages == 1:
                    # req = self._make_call(url_override=req.get("next"))
                    # ret.extend(req["results"])
                    return ret
                else:
                    self.concurrent_get(ret, page_size, page_range)
                return ret
            return ret
        else:
            return req

    def put(self, json=None, data=None) -> RequestResponse:
        """Makes PUT request.
        Makes a PUT request to Firemon API. Not sure why we have PUT statements
        with no data but it is what it is.

        Kwargs:
            json (dict): Contains a dict that will be turned into a json object and sent to the API.
            data (dict): x-form-url

        Raises:
            RequestError: if req.ok returns false.

        Returns:
            dict: data from the endpoint.
        """
        return self._make_call(verb="put", json=json, data=data)

    def post(self, json=None, data=None, files=None) -> RequestResponse:
        """Makes POST request.
        Makes a POST request to Firemon API.

        Kwargs:
            json (dict): Contains a dict that will be turned
            into a json and sent to the API.
            data (dict): x-form-url
            files (list/dict): See `Requests` how-to
            list of tuples formatted: ('file', bytes, 'text/plain')) or ('file', ('<file-name>', open(<path_to_file>, 'rb'))
            dict formatted: {'file': bytes} or {'file': ('<file-name>', open(<path_to_file>, 'rb')} or  {'devicepack.jar': bytes}

        Raises:
            RequestError: if req.ok returns false.

        Returns:
            dict: data from the endpoint.
        """
        return self._make_call(verb="post", json=json, data=data, files=files)

    def delete(self) -> bool:
        """Makes DELETE request.
        Makes a DELETE request to Firemon API.

        Returns:
            (bool) True if successful.

        Raises:
            RequestError if req.ok doesn't return True.
        """
        return self._make_call(verb="delete")

    def get_count(self) -> int:
        """Returns object count for query
        returns the value of the "total" field.

        Return:
            (int): number of objects query returned

        Raise:
            RequestError if req.ok returns false.
            ContentError if response is not json.
        """

        return self._make_call()["total"]

    def get_content(self) -> bytes:
        """Get content

        Warning:
            In some cases the appending of default pageSize my break our API calls.
            Appears to happen when requesting data blobs but not always.
        """
        log.info(f"GET: {self.url}")

        req = getattr(self.session, "get")(self.url, verify=self.verify)
        if req.ok:
            return req.content
        else:
            raise RequestError(req)

    def post_cpl_auth(self, data=None):
        """Authorize to the Control Panel and get Cookie Jar"""
        log.info(f"POST: {self.url}")

        req = getattr(self.session, "post")(self.url, data=data, verify=self.verify)
        if req.ok:
            return req
        else:
            raise RequestError(req)
