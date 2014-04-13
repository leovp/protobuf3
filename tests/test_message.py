from protobuf3.message import Message
from unittest import TestCase


class TestMessage(TestCase):

    def test_decode_field_signature(self):
        tmp = Message()

        data = [0b0001000]
        self.assertEqual(tmp._decode_field_signature(iter(data)), (0, 1, None))

        data = [0x12, 0x07]
        self.assertEqual(tmp._decode_field_signature(iter(data)), (2, 2, 7))

        data = [0b00001011]
        self.assertRaises(NotImplementedError, tmp._decode_field_signature, iter(data))

        data = [0b00001111]
        self.assertRaises(ValueError, tmp._decode_field_signature, iter(data))

    def test_decode_varint(self):
        tmp = Message()

        data = [0b00000001]
        self.assertEqual(tmp._decode_varint(iter(data)), 1)

        data = [0b10010110,  0b00000001]
        self.assertEqual(tmp._decode_varint(iter(data)), 150)

        data = [0b10101100, 0b00000010]
        self.assertEqual(tmp._decode_varint(iter(data)), 300)
