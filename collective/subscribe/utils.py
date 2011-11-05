from zope import schema
from zope.schema.fieldproperty import FieldProperty


def bind_field_properties(cls_locals, iface):
    for name, field in schema.getFieldsInOrder(iface):
        cls_locals[name] = FieldProperty(field)

valid_signature = lambda v: (isinstance(v, tuple) and 
                             len(v) == 2 and
                             isinstance(v[0], str) and
                             isinstance(v[1], str))

