#!/usr/bin/env python
# Copyright (c) 2011 Jan Kaliszewski (zuo). Available under the MIT License.

"""
namedtuple_with_abc.py:
* named tuple mix-in + ABC (abstract base class) recipe,
* works under Python 2.6, 2.7 as well as 3.x.

For details see

https://code.activestate.com/recipes/577629-namedtupleabc-abstract-base-class-mix-in-for-named/

"""

import collections
from abc import ABCMeta, abstractproperty
from functools import wraps
from sys import version_info

__all__ = ('namedtuple',)
_namedtuple = collections.namedtuple


class _NamedTupleABCMeta(ABCMeta):
    '''The metaclass for the abstract base class + mix-in for named tuples.'''
    def __new__(mcls, name, bases, namespace):
        fields = namespace.get('_fields')
        for base in bases:
            if fields is not None:
                break
            fields = getattr(base, '_fields', None)
        if not isinstance(fields, abstractproperty):
            basetuple = _namedtuple(name, fields)
            bases = (basetuple,) + bases
            namespace.pop('_fields', None)
            namespace.setdefault('__doc__', basetuple.__doc__)
            namespace.setdefault('__slots__', ())
        return ABCMeta.__new__(mcls, name, bases, namespace)


exec(
    # Python 2.x metaclass declaration syntax
    """class _NamedTupleABC(object):
        '''The abstract base class + mix-in for named tuples.'''
        __metaclass__ = _NamedTupleABCMeta
        _fields = abstractproperty()""" if version_info[0] < 3 else
    # Python 3.x metaclass declaration syntax
    """class _NamedTupleABC(metaclass=_NamedTupleABCMeta):
        '''The abstract base class + mix-in for named tuples.'''
        _fields = abstractproperty()"""
)


_namedtuple.abc = _NamedTupleABC
#_NamedTupleABC.register(type(version_info))  # (and similar, in the future...)

@wraps(_namedtuple)
def namedtuple(*args, **kwargs):
    '''Named tuple factory with namedtuple.abc subclass registration.'''
    cls = _namedtuple(*args, **kwargs)
    _NamedTupleABC.register(cls)
    return cls

collections.namedtuple = namedtuple


