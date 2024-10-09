"""
Management for a singleton metaclass
"""
import inspect
import pprint
from gc import get_referrers

import omni.graph.tools as ogt

# Unique constant that goes in the module's dictionary so that it can be filtered out
__SINGLETON_MODULE = True


class Singleton(type):
    """
    Helper for defining a singleton class in Python. You define it by starting
    your class as follows:

        from Singleton import Singleton
        class MyClass(metaclass=Singleton):
            # rest of implementation

    Then you can do things like this:

        a = MyClass()
        a.var = 12
        b = MyClass()
        assert b.var == 12
        assert a == b
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Construct the unique instance of the class if necessary, otherwise return the existing one"""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

    @staticmethod
    def forget(instanced_cls):
        """Removes the singleton class from the list of allocated singletons"""
        try:
            # Caller will usually be the class's destroy() function, invoker has a reference to the object
            # on which the destroy function is being called (which it will presumably remove after calling)
            (caller, invoker) = inspect.stack()[1:3]  # noqa: PLW0632
            referrers = []
            # Filter our the class's reference to itself as that is about to be destroyed
            for referrer in get_referrers(instanced_cls._instances[instanced_cls]):  # noqa: PLW0212
                try:
                    if referrer.f_back not in (caller.frame, invoker.frame):
                        referrers.append(referrer.f_back)
                except AttributeError:
                    if isinstance(referrer, dict):
                        if instanced_cls in referrer:
                            continue
                        if "__SINGLETON_MODULE" in referrer:
                            continue
                    referrers.append(referrer)
            if referrers:
                referrers = pprint.PrettyPrinter(indent=4).pformat(referrers)
                ogt.dbg_gc(f"Singleton {instanced_cls.__name__} has dangling references {referrers}")
            else:
                ogt.dbg_gc(f"Singleton {instanced_cls.__name__} cleanly forgotten")
            del instanced_cls._instances[instanced_cls]  # noqa: PLW0212
        except (AttributeError, KeyError) as error:
            ogt.dbg_gc(f"Failed trying to destroy singleton type {instanced_cls} - {error}")
