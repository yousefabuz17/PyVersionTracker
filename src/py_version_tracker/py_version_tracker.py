import re
import sys
import asyncio
import operator
import pypistats
import operator
from platform import _sys_version
from itertools import tee
from bs4 import BeautifulSoup
from collections import namedtuple
from functools import cache, cached_property
from typing import (Any, List, NoReturn, Tuple,
                    Match, Coroutine, Union,
                    NamedTuple, Generator, Iterator)
from aiohttp import (ClientSession, TCPConnector,
                    ClientConnectionError, ClientResponseError,
                    ServerConnectionError, ServerDisconnectedError)


class PyVersionException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)


class PyVersionTracker:
    _MAIN_PG = 'https://www.python.org/downloads'
    
    def __init__(self):
        pass
    
    @classmethod
    def _compiler(cls,
                __defaults, __k,
                *,
                escape_default=True,
                escape_k=True,
                search=True) -> Match:
        """
        ### Validate if the given input matches the provided defaults.
        
        Args:
            __defaults: Default values to match against (may contain regex patterns).
            __k: Input to validate.
            escape_k: Whether to escape special characters in the input (default is True).
            search: If True, perform a search; if False, perform a match (default is True).
        
        Returns:
            bool: True if the input matches any default, False otherwise.
        """
        if any((not __k,
                not isinstance(__k, str),
                hasattr(__k, '__str__'))):
            esc_k = str(__k)
        
        defaults = map(re.escape, map(str, __defaults))
        flag = '|' if escape_default else ''
        pattern = f'{flag}'.join(defaults)
        if escape_k:
            esc_k = '|'.join(map(re.escape, __k))
        
        compiler = re.compile(pattern, re.IGNORECASE)
        if not search:
            compiled = compiler.match(esc_k)
        else:
            compiled = compiler.search(esc_k)
        return compiled
    
    @classmethod
    @cache
    async def _request_py(cls, __url: str='') -> Union[Coroutine[Any, Any, str], NoReturn]:
        """Make an asynchronous HTTP request to a specified URL.
        
        Args:
            __url: URL for the HTTP request.
        
        Returns:
            Union[Coroutine[Any, Any, str], NoReturn]: Asynchronous HTTP response content.
        
        Raises:
            PyVersionException: Raised if the HTTP request fails.
        """
        url_link = __url or cls._MAIN_PG
        try:
            async with ClientSession(connector=TCPConnector(ssl=False,
                                                            ttl_dns_cache=300,
                                                            force_close=True,
                                                            enable_cleanup_closed=True),
                                    raise_for_status=True) as session:
                async with session.get(url_link) as response:
                    return await response.text()
        except (ServerDisconnectedError, ClientResponseError,
                ServerConnectionError, ClientConnectionError) as response_errors:
            raise PyVersionException(
                f'Failed trying to extract: {url_link}'
            ) from response_errors
    
    @classmethod
    def _parse_py(cls, __soup, attr='find_all', **kwargs) -> Any:
        return getattr(__soup, attr)(**kwargs)
    
    @classmethod
    @cache
    def _soupify(cls, __url='') -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup.

        Args:
            __soup: BeautifulSoup object containing HTML content.
            attr (str): Attribute to use for parsing (default is 'find_all').
            **kwargs: Additional keyword arguments for BeautifulSoup.

        Returns:
            Any: Result of the parsing operation.

        Raises:
            None
        """
        html_contents = asyncio.run(PyVersionTracker._request_py(__url))
        return BeautifulSoup(html_contents, 'html.parser')
    
    def _clean_page(self, **kwargs) -> List[str]:
        url = kwargs.pop('url', '')
        return [i.get_text(strip=True) for i in self._parse_py(self._soupify(url), **kwargs)]
    
    def _parse_mp(self, **kwargs) -> List[str]:
        return self._clean_page(name=kwargs.pop('name', 'span'), **kwargs)
    
    @staticmethod
    def _default_slicer(__start=1) -> slice:
        return slice(__start, *[None]*2)
    
    @cached_property
    def max_stable_version(self) -> NamedTuple:
        version_html: List[str] = self._parse_mp(name='p', class_='download-buttons', attr='find')
        max_version: str = version_html[1].split()[-1]
        return next(ver for ver in self.all_versions
                    if ver.version==max_version)
    
    @cached_property
    def min_stable_version(self) -> NamedTuple:
        return min(self.active_versions,
                key=lambda _x: self.str2tuple(_x.version))
    
    def _base_pytuple(self, __data, with_deprecation=False):
        """Create base namedtuple for PyVersion.

        Args:
            __data: Data to populate the namedtuple.
            with_deprecation (bool): Flag to include deprecation information (default is False).

        Returns:
            Generator: Generator of namedtuples.

        Raises:
            None
        """
        py_version = namedtuple('PyVersion',
                            ('version', 'release_date', 'deprecated'),
                            defaults=[None]*3)
        return (py_version(i[0], i[1], self.is_deprecated(i[0])) for i in __data) \
                if with_deprecation else (py_version(*i) for i in __data)
    
    @cached_property
    def all_versions(self) -> Generator[NamedTuple, None, None]:
        """Get all stable versions with deprecation information.

        Returns:
            Generator: Generator of namedtuples.

        Raises:
            None
        """
        return self._base_pytuple(self._get_all_versions(), with_deprecation=True)
    
    def _get_all_versions(self) -> Generator[NamedTuple, None, None]:
        get_contents = lambda __kind: self._parse_mp(class_=__kind)[self._default_slicer()]
        stable_versions = zip([i.split()[-1] for i in get_contents('release-number')],
                            get_contents('release-date'))
        return self._base_pytuple(stable_versions)
    
    @cached_property
    def active_versions(self) -> Generator[NamedTuple, None, None]:
        """Get active versions with status information.

        Returns:
            Generator: Generator of namedtuples.

        Raises:
            None
        """
        active_tuple = namedtuple('PyActive', ('version', 'status',
                                                'start', 'end', 'schedule'))
        get_contents = lambda __kind: self._parse_mp(class_=__kind)[self._default_slicer()]
        active_versions = zip(
                            get_contents('release-version'),
                            get_contents('release-status'),
                            get_contents('release-start'),
                            get_contents('release-end'),
                            get_contents('release-pep')
                            )
        return (active_tuple(*i) for i in active_versions)
    
    @classmethod
    def _base_error(cls) -> NoReturn:
        """Raise an exception for versions outside the accepted range.

        Raises:
            PyVersionException: Exception with an error message.
        """
        raise PyVersionException(
                    "The specified version is outside the accepted range of Python versions. "
                    "Please ensure that the provided version is included in the 'all_versions' range."
                    ) from None
    
    @classmethod
    def _validate_version(cls, __version: str) -> Union[str, NoReturn]:
        """Validate and format a given version string.

        Args:
            __version: Version string to validate.

        Returns:
            Union[str, NoReturn]: Validated and formatted version string.

        Raises:
            PyVersionException: Raised for invalid version formats.
        """
        compiler = lambda __pat: re.compile(__pat).match(__version)
        if compiler(r'^\d+\.\d+\.\d+$'):
            version: str = __version
        elif compiler(r'^\d+\.\d+$'):
            if cls.is_version(version:=(__version + '.0')):
                pass
        elif len(cls.str2tuple(__version))==3:
            pass
        else:
            raise PyVersionException(
                f'Invalid version format: {__version!r}.\n'
                'Please use the format X.Y.Z or X.Y.'
                )
        return version
    
    @classmethod
    def is_version(cls, __version: str) -> Union[bool, NoReturn]:
        """Check if a version is in the accepted range of Python versions.

        Args:
            __version: Version string to check.

        Returns:
            Union[bool, NoReturn]: True if the version is valid, raises exception otherwise.

        Raises:
            PyVersionException: Raised for invalid versions.
        """
        all_versions: Generator[str, None, None] = cls._unpack_versions(cls()._get_all_versions())
        if org_version:=(cls._validate_version(__version)):
            ver_compiled = cls._compiler(all_versions,
                                        __version,
                                        escape_k=False,
                                        search=False)
            if ver_compiled:
                found_version = ver_compiled.group(0)
                return found_version == org_version
        
        cls._base_error()
    
    @classmethod
    def is_deprecated(cls, __version: str) -> Union[bool, NoReturn]:
        """Check if a version is deprecated.

        Args:
            __version: Version string to check.

        Returns:
            Union[bool, NoReturn]: True if the version is deprecated, raises exception otherwise.

        Raises:
            PyVersionException: Raised for invalid versions.
        """
        version: str = cls._validate_version(__version)
        if version:
            unsupported: Generator[str, None, None] = cls._unpack_versions(cls._unsupported_v())
            all_v: Generator[str, None, None] = cls._unpack_versions(cls._unsupported_v(True))
            if version not in all_v:
                cls._base_error()
            else:
                return version in unsupported
    
    @classmethod
    def _unpack_versions(cls, __gen) -> Generator[str, None, None]:
        """Unpack versions from a generator.

        Args:
            __gen: Generator containing versions.

        Returns:
            Generator: Generator of version strings.

        Raises:
            None
        """
        return (ver.version for ver in __gen)
    
    @classmethod
    def _convert_tuple(cls, __version: str, tuple2str=False) -> Union[Tuple[int, ...], str]:
        """Convert a version string to a tuple of integers or a string.

        Args:
            __version (str): Version string to convert.
            tuple2str (bool, optional): If True, converts a version string to Tuple[int, ...]; if False, convert to a string. Defaults to True.

        Returns:
            Union[Tuple[int, ...], str]: Converted version as a tuple of integers or a string.

        Raises:
            PyVersionException: Raised for invalid version formats.
        """
        
        error: str = '''Please ensure the version follows the format: \
                        1) X.Y.Z or X.Y.
                        2) (X, Y, Z) or (X, Y)'''
            
        try:
            
            if tuple2str:
                version_parts: Tuple[int, ...] = '.'.join(map(int, __version.split('.')))
            else:
                version_parts: str = tuple(map(int, __version.split('.')))
            
            if len(version_parts) not in (2, 3):
                raise PyVersionException(
                    f"Invalid version format for ({version_parts}). {error}"
                    )
            return version_parts
        except ValueError as val_error:
            raise PyVersionException(
                f'The provided version ({__version!r}) cannot be interpreted as a valid version. \n'
                f'{val_error}'
            ) from val_error
    
    @classmethod
    def str2tuple(cls, __version: str):
        return cls._convert_tuple(__version)
    
    @classmethod
    def tuple2str(cls, __version: str):
        return cls._convert_tuple(__version, tuple2str=True)
    
    @classmethod
    def version_range(cls, __version: str=None, above=False):
        """Get versions within a specified range.

        Args:
            __version: Target version for the range (default is minimum stable version).
            above: Flag to get versions above the target version (default is False).

        Returns:
            Generator: Generator of version strings.

        Raises:
            None
        """
        if not __version:
            __version: str = cls().min_stable_version.version
        version: str = cls._validate_version(__version)
        target_version: Tuple[int, ...] = cls.tuple2str(version)
        _operator = operator.ge if above else operator.le
        return (ver for ver in cls().all_versions
                if _operator(cls.tuple2str(ver.version), target_version))
    
    @classmethod
    def _unsupported_v(cls, __all=False) -> Union[Iterator[NamedTuple],
                                            Generator[NamedTuple, None, None]]:
        all_versions: Tuple[tee, ...] = tee(cls()._get_all_versions())
        if __all:
            return all_versions[0]
        active_versions: List[str] = [i.version for i in cls().active_versions]
        last_active: str = cls._validate_version(active_versions.pop())
        versions: List[str] = sorted(cls._unpack_versions(all_versions[0]), key=cls.str2tuple)
        unsupported_v: List[str] = versions[:versions.index(last_active)]
        return (i for i in all_versions[1]
                if i.version in unsupported_v)
    
    @cached_property
    def unsupported_versions(self) -> Union[Iterator[NamedTuple],
                                    Generator[NamedTuple, None, None]]:
        """Get unsupported versions.

        Returns:
            Generator: Generator of version strings.

        Raises:
            None
        """
        return self._unsupported_v()
    
    @classmethod
    def package_tracker(cls, method: str='overall', **kwargs) -> Any:
        """Track package download statistics using pypistats.

        Args:
            method: Tracking method to use (default is 'overall').
            **kwargs: Additional keyword arguments for the tracking method.

        Returns:
            None

        Raises:
            PyVersionException: Raised for invalid tracking methods.
        """
        try:
            return getattr(pypistats, method)(**kwargs)
        except AttributeError as attr_error:
            raise PyVersionException(attr_error)
    
    @classmethod
    def version_checker(cls, __sys_version=None, minimum_version=None) -> Union[bool, NoReturn]:
        """Check if the current Python version meets the specified minimum requirements.

        This method compares the provided system version with the minimum required version
        for optimal functionality. If the system version is less than the minimum required version,
        a PyVersionException is raised, indicating the incompatibility and recommending an upgrade.

        Args:
            __sys_version (str, optional): The system version to check (default is the current Python version).
            minimum_version (str, optional): The minimum required version (default is the minimum stable version).

        Returns:
            Union[bool, NoReturn]: True if the system version meets the minimum requirements.

        Raises:
            PyVersionException: Raised if the system version is below the minimum required version.
        """
        if __sys_version is None:
            __sys_version = sys.version
        
        if minimum_version is None:
            minimum_version = cls().min_stable_version.version
        
        sys_version = _sys_version(__sys_version)[1]
        min_version = cls._validate_version(minimum_version)
        less_than = operator.lt(*map(cls.str2tuple, (sys_version, min_version)))
        if less_than:
            raise PyVersionException(
            f"{cls.__name__!r} requires Python {min_version!r} or a more recent version for optimal functionality.\n"
            f"Your current Python version is {sys_version!r}, which has been assessed and flagged as potentially incompatible.\n"
            "Kindly consider upgrading your Python installation to meet the minimum required version and attempt the operation again."
            )
        
        return True

PyVersionTracker.version_checker(sys.version, '3.8')

__all__ = ('PyVersionTracker', 'PyVersionException')
__version__ = "0.0.1"
__author__ = "Yousef Abuzahrieh <yousef.zahrieh17@gmail.com"

__doc__ = """
PyVersionTracker: Python Version Information Tracker

This module provides a Python version information tracker that fetches and parses data from the official Python downloads page (https://www.python.org/downloads).
It uses asynchronous HTTP requests, BeautifulSoup for HTML parsing, and provides functionalities to extract information about stable and active Python versions,
including their release dates, deprecation status, and more.

Classes:
    - PyVersionTracker: Main class for tracking Python version information.
    - PyVersionException: Custom exception class for handling errors in PyVersionTracker.

Module Dependencies:
    - re: Regular expression library for pattern matching.
    - asyncio: Asynchronous programming library.
    - operator: Standard operators as functions.
    - pypistats: Library for fetching Python package download statistics.
    - itertools: Functions creating iterators for efficient looping.
    - bs4 (BeautifulSoup): Library for pulling data out of HTML and XML files.
    - collections: Additional data structures.
    - functools: Higher-order functions and operations on callable objects.
    - typing: Support for type hints.

Attributes:
    - __all__: Tuple containing names exported by the module.
    - __version__: Version of the PyVersionTracker module.
    - __author__: Author information.

Classes:
    - PyVersionException: Custom exception class for PyVersionTracker.

Methods:
    - PyVersionTracker.max_stable_version: Get the latest stable version.
    - PyVersionTracker.min_stable_version: Get the minimum stable version.
    - PyVersionTracker.all_versions: Get all stable versions with deprecation information.
    - PyVersionTracker.active_versions: Get active versions with status information.
    - PyVersionTracker.is_version: Check if a version is in the accepted range of Python versions.
    - PyVersionTracker.is_deprecated: Check if a version is deprecated.
    - PyVersionTracker.str2tuple: Convert a version string to a tuple of integers.
    - PyVersionTracker.version_range: Get versions within a specified range.
    - PyVersionTracker.unsupported_versions: Get unsupported versions.
    - PyVersionTracker.package_tracker: Track package download statistics using pypistats.

Example Usage:
    - Instantiate PyVersionTracker: tracker = PyVersionTracker()
    - Access information: latest_version = tracker.max_stable_version
    - Track package download statistics: PyVersionTracker.package_tracker(package='cipher-engine', verbose=True)

Author:
    - Yousef Abuzahrieh <yousef.zahrieh17@gmail.com>

Version:
    - 0.0.1
"""


# print(PyVersionTracker().min_stable_version)
# print(PyVersionTracker().tuple2str('2.0.8'))
print(PyVersionTracker().version_checker())
# print(list(PyVersionTracker.version_range('3.9')))
# print(pypistats.overall('cipher-engine'))
# print(pypistats.pypi_stats_api('packages/cipher-engine/recent', verbose=True))
# print(PyVersionTracker.package_tracker(package='cipher-engine', verbose=True))
# print(sorted(PyVersionTracker().all_versions, key=lambda x: PyVersionTracker.str2tuple(x.version)))
# print(PyVersionTracker().is_version('2.0.11'))
# print(PyVersionTracker().is_deprecated('3.8.6'))
# print(list(PyVersionTracker().active_versions))