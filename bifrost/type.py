from typing import NamedTuple
from thundersnow.precondition import check_argument
from thundersnow.predicate import is_not_blank


class Version(NamedTuple):
    """Sematnic Version object"""
    major: str
    minort: str
    patch: str

    def __str__(self):
        return '.'.join(self)


def from_string(s):
    """ '1.2.3' -> Version('1','2','3')"""
    s = str(s)
    check_argument((s is not None) and is_not_blank(s), 'cannot create version from blank string')
    parts = s.split('.')
    if len(parts) == 1:
        major, minor, patch = (parts[0], 0, 0)
    elif len(parts) == 2:
        major, minor, patch = (parts[0], parts[1], 0)
    elif len(parts) == 3:
        major, minor, patch = parts
    else:
        major, minor, patch = parts[:3]

    major, minor, patch = [str(i) for i in (major, minor, patch)]
    return Version(major, minor, patch)

Version.from_string = from_string