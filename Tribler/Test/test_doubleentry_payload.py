import unittest

from Tribler.community.doubleentry.payload import encode_signing_format


class TestSigningFormat(unittest.TestCase):

    def test_prepare_for_signing(self):
        # Arrange
        data = ("abc", 12, "def")
        # Act
        result = encode_signing_format(data)
        # Assert
        self.assertEqual("abc.12.def", result)