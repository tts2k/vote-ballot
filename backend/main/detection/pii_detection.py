import re

from ..objects.voter import Voter, decrypt_name

REDACTED_PHONE_NUMBER = "[REDACTED PHONE NUMBER]"
REDACTED_NAME = "[REDACTED NAME]"
REDACTED_EMAIL = "[REDACTED EMAIL]"
REDACTED_NATIONAL_ID = "[REDACTED NATIONAL ID]"
PHONE_NUMBER_REGEX = re.compile(
    r"(?<!\d)(\b|\()?\d{3}\)?(-|\s)?\d{3}(-|\s)?\d{4}\b(?!\d)"
)
EMAIL_REGEX = re.compile(r"\b\S+@\S+\.\S+\b")
NATIONAL_ID_REGEX = re.compile(r"\b\d{3}(-|\s)?[\s\d]{2}(-|\s)?[\d]{4}\b")


def redact_free_text(free_text: str, voter: Voter) -> str:
    """
    :param: free_text The free text to remove sensitive data from
    :returns: The redacted free text
    """

    first_name = decrypt_name(voter.first_name)
    last_name = decrypt_name(voter.last_name)

    new_text = free_text.replace(first_name, REDACTED_NAME).replace(
        last_name, REDACTED_NAME
    )

    new_text = PHONE_NUMBER_REGEX.sub(REDACTED_PHONE_NUMBER, new_text)
    new_text = EMAIL_REGEX.sub(REDACTED_EMAIL, new_text)
    new_text = NATIONAL_ID_REGEX.sub(REDACTED_NATIONAL_ID, new_text)

    return new_text
