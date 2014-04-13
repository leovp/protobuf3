from collections import namedtuple
from functools import reduce


WireField = namedtuple('WireField', ['type', 'value'])


class Message(object):
    FIELD_VARINT = 0
    FIELD_FIXED64 = 1
    FIELD_VARIABLE_LENGTH = 2
    FIELD_START_GROUP = 3
    FIELD_END_GROUP = 4
    FIELD_FIXED32 = 5

    def __init__(self):
        self.__wire_message = {}

    @staticmethod
    def _decode_field_signature(input_iterator):
        number = Message._decode_varint(input_iterator)

        field_type = number & 0b111
        field_number = number >> 3

        if field_type == Message.FIELD_VARIABLE_LENGTH:
            field_length = Message._decode_varint(input_iterator)
        elif field_type in (Message.FIELD_START_GROUP, Message.FIELD_END_GROUP):
            raise NotImplementedError("Groups is deprecated and unsupported in protobuf3")
        elif field_type in (Message.FIELD_VARINT, Message.FIELD_FIXED64, Message.FIELD_FIXED32):
            field_length = None
        else:
            raise ValueError("Unknown wire type")

        return field_type, field_number, field_length

    @staticmethod
    def _decode_varint(input_iterator):
        result = []
        while True:
            next_byte = next(input_iterator)
            result.append(next_byte & 0b01111111)
            if not next_byte & (1 << 7):
                return reduce(lambda a, b: a + b,
                              map(lambda a, b: a * b,
                                  result,
                                  [(1 << 7) ** i for i in range(len(result))]
                              )
                )

    def _decode_raw_message(self, input_iterator):
        try:
            while True:
                field_type, field_number, field_length = Message._decode_field_signature(input_iterator)

                if field_type == Message.FIELD_VARINT:
                    field_value = Message._decode_varint(input_iterator)
                else:
                    raise NotImplementedError

                self.__wire_message[field_number] = WireField(type=field_type, value=field_value)
        except StopIteration:
            pass
