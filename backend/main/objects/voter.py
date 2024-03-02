#
# This file contains classes that correspond to voters
#


import hashlib
from base64 import b64decode, b64encode
from enum import Enum

import jsons
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from ..store import secret_registry

NAME_ENCRYPTION_KEY_AES_SIV = "NAME_ENCRYPTION_KEY_AES_SIV"


def obfuscate_national_id(national_id: str) -> str:
    """
    Minimizes a national ID. The minimization may be either irreversible or reversible, but one might make life easier
    that the other, depending on the use-cases.

    :param: national_id A real national ID that is sensitive and needs to be obfuscated in some manner.
    :return: An obfuscated version of the national_id.
    """

    sanitized_national_id = national_id.replace("-", "").replace(" ", "").strip()
    return hashlib.sha256(sanitized_national_id.encode("utf-8")).hexdigest()


def encrypt_name(name: str) -> str:
    """
    Encrypts a name, non-deterministically.


    :param: name A plaintext name that is sensitive and needs to encrypt.
    :return: The encrypted cipher text of the name.
    """
    expected_bytes = 32
    name_encryption_key = secret_registry.get_secret_bytes(NAME_ENCRYPTION_KEY_AES_SIV)
    if not name_encryption_key:
        name_encryption_key = get_random_bytes(expected_bytes * 2)
        secret_registry.overwrite_secret_bytes(
            NAME_ENCRYPTION_KEY_AES_SIV, name_encryption_key
        )

    nonce = get_random_bytes(expected_bytes)
    cipher = AES.new(name_encryption_key, AES.MODE_SIV, nonce=nonce)

    cipher.update(b"")
    ciphertext, tag = cipher.encrypt_and_digest(name.encode("utf-8"))

    json_v = [b64encode(x).decode("utf-8") for x in (nonce, ciphertext, tag)]
    return jsons.dumps(dict(zip(["nonce", "ciphertext", "tag"], json_v)))


def decrypt_name(encrypted_name: str) -> str:
    """
    Decrypts a name. This is the inverse of the encrypt_name method above.

    :param: encrypted_name The ciphertext of a name that is sensitive
    :return: The plaintext name
    """
    name_encryption_key = secret_registry.get_secret_bytes(NAME_ENCRYPTION_KEY_AES_SIV)
    if name_encryption_key is None:
        raise Exception()

    b64 = jsons.loads(encrypted_name)
    json_dict = {k: b64decode(b64[k]) for k in ["nonce", "ciphertext", "tag"]}
    cipher = AES.new(name_encryption_key, AES.MODE_SIV, nonce=json_dict["nonce"])
    cipher.update(b"")

    return cipher.decrypt_and_verify(json_dict["ciphertext"], json_dict["tag"]).decode(
        "utf-8"
    )


class MinimalVoter:
    """
    Our representation of a voter, with the national id obfuscated (but still unique).
    This is the class that we want to be using in the majority of our codebase.
    """

    def __init__(
        self,
        obfuscated_first_name: str,
        obfuscated_last_name: str,
        obfuscated_national_id: str,
        voted: bool,
        fraud_commited: bool,
    ):
        self.obfuscated_national_id = obfuscated_national_id
        self.obfuscated_first_name = obfuscated_first_name
        self.obfuscated_last_name = obfuscated_last_name
        self.voted = voted
        self.fraud_commited = fraud_commited


class Voter:
    """
    Our representation of a voter, including certain sensitive information.=
    This class should only be used in the initial stages when requests come in; in the rest of the
    codebase, we should be using the ObfuscatedVoter class
    """

    def __init__(
        self,
        first_name: str,
        last_name: str,
        national_id: str,
        voted=False,
        fraud_commited=False,
    ):
        self.national_id = national_id
        self.first_name = first_name
        self.last_name = last_name
        self.voted = voted
        self.fraud_commited = fraud_commited

    def get_minimal_voter(self) -> MinimalVoter:
        """
        Converts this object (self) into its obfuscated version
        """
        return MinimalVoter(
            encrypt_name(self.first_name.strip()),
            encrypt_name(self.last_name.strip()),
            obfuscate_national_id(self.national_id),
            self.voted,
            self.fraud_commited,
        )


class VoterStatus(Enum):
    """
    An enum that represents the current status of a voter.
    """

    NOT_REGISTERED = "not registered"
    REGISTERED_NOT_VOTED = "registered, but no ballot received"
    BALLOT_COUNTED = "ballot counted"
    FRAUD_COMMITTED = "fraud committed"


class BallotStatus(Enum):
    """
    An enum that represents the current status of a voter.
    """

    VOTER_BALLOT_MISMATCH = "the ballot doesn't belong to the voter specified"
    INVALID_BALLOT = "the ballot given is invalid"
    FRAUD_COMMITTED = "fraud committed: the voter has already voted"
    VOTER_NOT_REGISTERED = "voter not registered"
    BALLOT_COUNTED = "ballot counted"
