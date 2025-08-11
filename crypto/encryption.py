"""Encryption utilities using quantum keys."""


class OneTimePad:
    """One-time pad encryption using quantum keys.

    This class implements the one-time pad encryption scheme, which is
    information-theoretically secure when used with a truly random key
    that is at least as long as the message and never reused.
    """

    @staticmethod
    def encrypt(message: str, key: list[int]) -> tuple[list[int], list[int]]:
        """Encrypt a message using the one-time pad.

        Args:
            message: Message to encrypt
            key: Binary key for encryption

        Returns:
            Tuple of (ciphertext, remaining_key)

        Raises:
            ValueError: If the key is shorter than the message

        """
        # Convert the message to binary
        message_bits = OneTimePad._text_to_bits(message)

        # Check if the key is long enough
        if len(key) < len(message_bits):
            raise ValueError("Key is too short for the message")

        # Use only the necessary part of the key
        used_key = key[: len(message_bits)]
        remaining_key = key[len(message_bits) :]

        # Encrypt the message using XOR
        ciphertext = [(m + k) % 2 for m, k in zip(message_bits, used_key, strict=False)]

        return ciphertext, remaining_key

    @staticmethod
    def encrypt_file(
        file_path: str, key: list[int], output_path: str = None
    ) -> tuple[str, list[int]]:
        """Encrypt a file using the one-time pad.

        Args:
            file_path: Path to the file to encrypt
            key: Binary key for encryption
            output_path: Path to save the encrypted file (optional)

        Returns:
            Tuple of (output_path, remaining_key)

        Raises:
            ValueError: If the key is shorter than the file
            FileNotFoundError: If the input file does not exist

        """
        # Read the file
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
        except FileNotFoundError as err:
            raise FileNotFoundError(f"File not found: {file_path}") from err

        # Convert the file data to binary
        file_bits = OneTimePad._bytes_to_bits(file_data)

        # Check if the key is long enough
        if len(key) < len(file_bits):
            raise ValueError("Key is too short for the file")

        # Use only the necessary part of the key
        used_key = key[: len(file_bits)]
        remaining_key = key[len(file_bits) :]

        # Encrypt the file using XOR
        ciphertext = [(m + k) % 2 for m, k in zip(file_bits, used_key, strict=False)]

        # Convert the ciphertext back to bytes
        ciphertext_bytes = OneTimePad._bits_to_bytes(ciphertext)

        # Determine the output path
        if output_path is None:
            output_path = file_path + ".enc"

        # Write the encrypted file
        with open(output_path, "wb") as f:
            f.write(ciphertext_bytes)

        return output_path, remaining_key

    @staticmethod
    def _text_to_bits(text: str) -> list[int]:
        """Convert text to a list of bits.

        Args:
            text: Text to convert

        Returns:
            List of bits representing the text

        """
        # Convert each character to its ASCII value, then to binary
        bits = []
        for char in text:
            ascii_value = ord(char)
            for i in range(8):
                bits.append((ascii_value >> (7 - i)) & 1)

        return bits

    @staticmethod
    def _bits_to_text(bits: list[int]) -> str:
        """Convert a list of bits to text.

        Args:
            bits: List of bits to convert

        Returns:
            Text represented by the bits

        """
        # Group bits into bytes (8 bits each)
        text = ""
        for i in range(0, len(bits), 8):
            if i + 8 <= len(bits):
                byte = bits[i : i + 8]
                ascii_value = sum(byte[j] << (7 - j) for j in range(8))
                text += chr(ascii_value)

        return text

    @staticmethod
    def _bytes_to_bits(data: bytes) -> list[int]:
        """Convert bytes to a list of bits.

        Args:
            data: Bytes to convert

        Returns:
            List of bits representing the bytes

        """
        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)

        return bits

    @staticmethod
    def _bits_to_bytes(bits: list[int]) -> bytes:
        """Convert a list of bits to bytes.

        Args:
            bits: List of bits to convert

        Returns:
            Bytes represented by the bits

        """
        # Group bits into bytes (8 bits each)
        bytes_data = bytearray()
        for i in range(0, len(bits), 8):
            if i + 8 <= len(bits):
                byte = bits[i : i + 8]
                byte_value = sum(byte[j] << (7 - j) for j in range(8))
                bytes_data.append(byte_value)

        return bytes(bytes_data)
