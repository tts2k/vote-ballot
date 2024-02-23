import re

from main.objects.voter import Voter

REDACTED_PHONE_NUMBER = "[REDACTED PHONE NUMBER]"
REDACTED_ID_NUMBER = "[REDACTED ID NUMBER]"
PHONE_NUMBER_REGEX = re.compile(
    r"(?<!\d)(\b|\()?\d{3}\)?(-|\s)?\d{3}(-|\s)?\d{4}\b(?!\d)"
)


def redact_free_text(free_text: str, voter: Voter) -> str:
    """
    :param: free_text The free text to remove sensitive data from
    :returns: The redacted free text
    """

    # TODO: Implement this! Feel free to change the function parameters if you need to
    raise NotImplementedError()
