from .base import BaseField
from protobuf3.message import Message


class MessageField(BaseField):
    WIRE_TYPE = Message.FIELD_VARIABLE_LENGTH

    def __init__(self, message_cls=None, **kwargs):
        self.__cls = message_cls
        super().__init__(**kwargs)

    @property
    def default_value(self):
        return self.__cls()

    def _convert_to_final_type(self, value):
        msg = self.__cls()
        msg.parse_from_bytes(value)

        return msg

    def _convert_to_wire_type(self, value):
        if value < 0:
            return 2 ** 64 + value

        return value

    def _validate(self, value):
        return False  # Direct assignment is forbidden
