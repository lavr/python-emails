# encoding: utf-8
from __future__ import unicode_literals
import pytest
from emails.smtp.factory import ObjectFactory


def test_object_factory():
    class A:
        """ Sample class for testing """

        def __init__(self, a, b=None):
            self.a = a
            self.b = b

    factory = ObjectFactory(cls=A)

    obj1 = factory[{'a': 1, 'b': 2}]
    assert isinstance(obj1, A)
    assert obj1.a == 1
    assert obj1.b == 2

    obj2 = factory[{'a': 1, 'b': 2}]
    assert obj2 is obj1

    obj3 = factory[{'a': 100}]
    assert obj3 is not obj1

    obj4 = factory.invalidate({'a': 100})
    assert obj3 != obj4
    assert obj3.a == obj4.a

    with pytest.raises(ValueError):
        factory[42]


