from .base import BaseField
from protobuf3.message import Message


class BytesField(BaseField):
    DEFAULT_VALUE = b''
    WIRE_TYPE = Message.FIELD_VARIABLE_LENGTH

    def _convert_to_final_type(self, value):
        return value

    def _convert_to_wire_type(self, value):
        if isinstance(value, str):
            value = value.encode()
        return value

    def _validate(self, value):
        return isinstance(value, (bytes, str))
