import base64
import collections
import importlib
import json
import marshal
import re
import types as _types


class TypedEncoder(json.JSONEncoder):
    def __init__(self, types, *args, **kwargs):
        self.types = types
        super().__init__(*args, **kwargs)

    def default(self, obj):
        ptype = obj.__class__
        if ptype in self.types:
            serializable = {'__python_type__': repr(ptype)}
            serializable['__data__'] = self.types[ptype][0](obj)
            return serializable

        return json.JSONEncoder.default(obj)


class ObjectHook:
    def __init__(self, types):
        self.types = {repr(k): v[1] for k, v in types.items()}

    def __call__(self, obj):
        ptype = obj.get('__python_type__')
        if ptype:
            return self.types[ptype](obj['__data__'])
        return obj


class Codec:
    def __init__(self, *types):
        retypes = {}
        for t in types:
            if isinstance(t, dict):
                retypes.update(t)
            else:
                retypes[t[0]] = t[1]
        self.encode = TypedEncoder(retypes).encode
        self.decode = json.JSONDecoder(object_hook=ObjectHook(retypes)).decode


# builtin tyoes
tuples = tuple, (list, tuple)
ranges = range, (lambda r: [r.start, r.stop, r.step],
                 lambda args: range(*args))
sets = set, (list, set)
frozensets = frozenset, (list, frozenset)


byteencode = base64.b64encode
bytedecode = base64.b64decode
bytes_obj = bytes, (lambda b: byteencode(b).decode('ascii'),
                    bytedecode)
bytearrays = bytearray, (bytes_obj[1][0],
                         lambda s: bytearray(bytedecode(s)))

code_obj = _types.CodeType, (
    lambda co: bytes_obj[1][0](marshal.dumps(co)),
    lambda s: marshal.loads(bytedecode(s)))

functions = _types.FunctionType, (
    lambda f: {
        'code': code_obj[1][0](f.__code__),
        'module': f.__module__,
        'defaults': f.__defaults__
    },
    lambda d: _types.FunctionType(
        code_obj[1][1](d['code']),
        vars(importlib.import_module(d['module'])),
        argdefs=tuple(d['defaults']) if d['defaults'] else None)
)

# regex
regexen = re.compile('').__class__, (
    lambda r: [r.pattern, r.flags],
    lambda l: re.compile(*l))

# collections
deques = collections.deque, (list, collections.deque)
chainmaps = collections.ChainMap, (lambda cm: cm.maps,
                                   lambda l: collections.ChainMap(*l))
counters = collections.Counter, (dict, collections.Counter)
ordereddicts = collections.OrderedDict, (
    lambda od: list(od.items), collections.OrderedDict)
