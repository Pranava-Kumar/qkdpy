"""Decryption utilities using quantum keys."""


class OneTimePadDecrypt:
    """One-time pad decryption using quantum keys.

    This class implements the one-time pad decryption scheme, which is
    information-theoretically secure when used with a truly random key
    that is at least as long as the message and never reused.
    """

    @staticmethod
    def decrypt(ciphertext: list[int], key: list[int]) -> str:
        """Decrypt a message using the one-time pad.

        Args:
            ciphertext: Ciphertext to decrypt
            key: Binary key for decryption

        Returns:
            Decrypted message

        Raises:
            ValueError: If the key is shorter than the ciphertext

        """
        # Check if the key is long enough
        if len(key) < len(ciphertext):
            raise ValueError("Key is too short for the ciphertext")

        # Use only the necessary part of the key
        used_key = key[: len(ciphertext)]

        # Decrypt the ciphertext using XOR
        message_bits = [(c + k) % 2 for c, k in zip(ciphertext, used_key, strict=False)]

        # Convert the message bits to text
        message = OneTimePadDecrypt._bits_to_text(message_bits)

        return message

    @staticmethod
    def decrypt_file(file_path: str, key: list[int], output_path: str = None) -> str:
        """Decrypt a file using the one-time pad.

        Args:
            file_path: Path to the file to decrypt
            key: Binary key for decryption
            output_path: Path to save the decrypted file (optional)

        Returns:
            Path to the decrypted file

        Raises:
            ValueError: If the key is shorter than the file
            FileNotFoundError: If the input file does not exist

        """
        # Read the encrypted file
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
        except FileNotFoundError as err:
            raise FileNotFoundError(f"File not found: {file_path}") from err

        # Convert the file data to binary
        file_bits = OneTimePadDecrypt._bytes_to_bits(file_data)

        # Check if the key is long enough
        if len(key) < len(file_bits):
            raise ValueError("Key is too short for the file")

        # Use only the necessary part of the key
        used_key = key[: len(file_bits)]

        # Decrypt the file using XOR
        message_bits = [(c + k) % 2 for c, k in zip(file_bits, used_key, strict=False)]

        # Convert the message bits back to bytes
        message_bytes = OneTimePadDecrypt._bits_to_bytes(message_bits)

        # Determine the output path
        if output_path is None:
            if file_path.endswith(".enc"):
                output_path = file_path[:-4]  # Remove the .enc extension
            else:
                output_path = file_path + ".dec"

        # Write the decrypted file
        with open(output_path, "wb") as f:
            f.write(message_bytes)

        return output_path

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
