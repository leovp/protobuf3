from collections import namedtuple
from functools import reduce
from protobuf3.fields.base import BaseField

WireField = namedtuple('WireField', ['type', 'value'])


class Message(object):
    FIELD_VARINT = 0
    FIELD_FIXED64 = 1
    FIELD_VARIABLE_LENGTH = 2
    FIELD_START_GROUP = 3
    FIELD_END_GROUP = 4
    FIELD_FIXED32 = 5

    __fields = None

    def __new__(cls, *args):
        if not cls.__fields:
            cls.__fields = {}
            for (field_name, field_object) in cls.__dict__.items():
                if isinstance(field_object, BaseField):
                    cls.__fields[field_object.field_number] = field_object
                    field_object.field_name = field_name

        return super().__new__(cls, *args)

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
    def _encode_field_signature(field_type, field_number, field_length=None):
        if field_type not in (
                Message.FIELD_VARINT, Message.FIELD_FIXED64, Message.FIELD_VARIABLE_LENGTH, Message.FIELD_FIXED32):
            raise ValueError("Unknown field type for serialization")

        result = Message._encode_varint((field_number << 3) | field_type)

        if field_type == Message.FIELD_VARIABLE_LENGTH:
            assert field_length

            result += Message._encode_varint(field_length)

        return result

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
                                  [(1 << 7) ** i for i in range(len(result))]))

    @staticmethod
    def _encode_varint(number):
        result = []

        while number:
            next_byte = number % 128
            number //= 128

            if number:
                next_byte |= 1 << 7
            result.append(next_byte)

        return bytes(result)

    def _decode_raw_message(self, input_iterator):
        def __read_n_bytes(n):
            result = bytearray()
            for _ in range(n):
                result.append(next(input_iterator))
            return bytes(result)

        try:
            while True:
                field_type, field_number, field_length = Message._decode_field_signature(input_iterator)
                field_object = self.__fields.get(field_number, BaseField(field_number))

                if field_type != field_object.WIRE_TYPE and field_object.WIRE_TYPE != -1:
                    raise ValueError

                if field_type == Message.FIELD_VARINT:
                    field_value = Message._decode_varint(input_iterator)
                elif field_type == Message.FIELD_FIXED64:
                    field_value = __read_n_bytes(8)
                elif field_type == Message.FIELD_VARIABLE_LENGTH:
                    field_value = __read_n_bytes(field_length)
                elif field_type == Message.FIELD_FIXED32:
                    field_value = __read_n_bytes(4)
                else:
                    raise NotImplementedError

                if field_number in self.__wire_message:
                    if self.__wire_message[field_number][0].type != field_type:
                        raise ValueError

                    self.__wire_message[field_number].append(WireField(type=field_type, value=field_value))
                else:
                    self.__wire_message[field_number] = [WireField(type=field_type, value=field_value)]
        except StopIteration:
            pass

    def _check_required_fields(self):
        missing_fields = []

        for (field_number, field_object) in self.__fields.items():
            if field_object.required and field_number not in self.__wire_message:
                missing_fields.append(field_object.field_name)

        if missing_fields:
            raise KeyError("Some required fields are missing: " + ", ".join(missing_fields))

    def _get_wire_values(self, field_number):
        return self.__wire_message.get(field_number, [])

    def _set_wire_values(self, field_number, field_type, field_value, index=None, insert=False, append=False):
        if field_number not in self.__wire_message:
            self.__wire_message[field_number] = []
        if append:
            self.__wire_message[field_number].append(WireField(type=field_type, value=field_value))
        elif insert:
            self.__wire_message[field_number].insert(index, WireField(type=field_type, value=field_value))
        elif index:
            self.__wire_message[field_number][index] = WireField(type=field_type, value=field_value)
        else:
            self.__wire_message[field_number] = [WireField(type=field_type, value=field_value)]

    def parse_from_bytes(self, bytes_array):
        self.__wire_message = {}
        input_iterator = iter(bytes_array)
        self._decode_raw_message(input_iterator)

        self._check_required_fields()

    def encode_to_bytes(self, ignore_unknown=False):
        self._check_required_fields()

        result = []

        for field_number in sorted(self.__wire_message.keys()):
            if ignore_unknown and field_number not in self.__fields:
                continue

            for it in self.__wire_message[field_number]:
                field_len = len(it.value) if it.type == Message.FIELD_VARIABLE_LENGTH else None

                result.append(Message._encode_field_signature(it.type, field_number, field_len))

                if it.type == Message.FIELD_VARINT:
                    result.append(Message._encode_varint(it.value))
                else:
                    result.append(it.value)

        return b''.join(result)
