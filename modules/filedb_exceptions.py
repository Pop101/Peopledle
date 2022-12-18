import os


def is_name_valid(key: str) -> bool:
    """Checks if the key is valid for the database

    Args:
        key (str): They key to check

    Returns:
        bool: True if the key is valid, False otherwise
    """

    if "." in key:
        return False
    if os.path.sep in key:
        return False
    return True


def validate_name(key: str) -> None:
    """Checks if the key is valid for the database, raises an exception if it is not

    Args:
        key (str): They key to check

    Returns:
        None
    """

    if not is_name_valid(key):
        raise FileDBInvalidName(f"Key {key} is not a valid key for the database")


class FileDBException(Exception):
    """Base class for all FileDB exceptions"""

    pass


class FileDBInvalidName(FileDBException):
    """Raised when the name of the database key is invalid"""

    pass
