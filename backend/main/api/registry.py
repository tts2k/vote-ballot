#
# This file is the internal-only API that allows for the population of the voter registry.
# This API should not be exposed as a REST API for election security purposes.
#
from typing import List

from ..objects.candidate import Candidate
from ..objects.voter import Voter, VoterStatus
from ..store.data_registry import VotingStore

#
# Voter Registration
#


def register_voter(voter: Voter) -> bool:
    """
    Registers a specific voter for the election. This method doesn't verify that the voter is eligible to vote or any
    such legal logistics -- it simply registers them if they aren't currently registered.

    :param: voter The voter to register.
    :returns: Boolean TRUE if the registration was successful. Boolean FALSE if the voter was already registered
              (based on their National ID)
    """
    store = VotingStore.get_instance()
    status = get_voter_status(voter.national_id)
    if status != VoterStatus.NOT_REGISTERED:
        return False

    store.add_voter(voter)
    return True


def get_voter_status(voter_national_id: str) -> VoterStatus:
    """
    Checks to see if the specified voter is registered.

    :param: voter_national_id The sensitive ID of the voter to check the registration status of.
    :returns: The status of the voter that best describes their situation
    """
    store = VotingStore.get_instance()
    existing_voter = store.get_voter_by_national_id(voter_national_id)

    if existing_voter is None:
        return VoterStatus.NOT_REGISTERED
    if existing_voter.fraud_commited:
        return VoterStatus.FRAUD_COMMITTED
    if existing_voter.voted:
        return VoterStatus.BALLOT_COUNTED

    return VoterStatus.REGISTERED_NOT_VOTED


def de_register_voter(voter_national_id: str) -> bool:
    """
    De-registers a voter from voting. This is to be used when the user requests to be removed from the system.
    If a voter is a fraudulent voter, this should still be reflected in the system; they should not be able to
    de-registered.

    :param: voter_national_id The sensitive ID of the voter to de-register.
    :returns: Boolean TRUE if de-registration was successful. Boolean FALSE otherwise.
    """
    store = VotingStore.get_instance()
    voter = store.get_voter_by_national_id(voter_national_id)

    if voter is None:
        return False
    if voter.fraud_commited:
        return False

    store.delete_voter_by_national_id(voter_national_id)
    return True


#
# Candidate Registration (Already Implemented)
#


def register_candidate(candidate_name: str):
    """
    Registers a candidate for the election, if not already registered.
    """
    store = VotingStore.get_instance()
    store.add_candidate(candidate_name)


def candidate_is_registered(candidate: Candidate) -> bool:
    """
    Checks to see if the specified candidate is registered.

    :param: candidate The candidate to check the registration status of
    :returns: Boolean TRUE if the candidate is registered. Boolean FALSE otherwise.
    """
    store = VotingStore.get_instance()
    return store.get_candidate(candidate.candidate_id) is not None


def get_all_candidates() -> List[Candidate]:
    store = VotingStore.get_instance()
    return store.get_all_candidates()
