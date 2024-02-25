from typing import Optional, Set

import bcrypt
from main.api.registry import get_voter_status
from main.detection.pii_detection import redact_free_text
from main.objects.ballot import Ballot, generate_ballot_number
from main.objects.candidate import Candidate
from main.objects.voter import BallotStatus, VoterStatus, decrypt_name
from main.store.data_registry import VotingStore


def issue_ballot(voter_national_id: str) -> Optional[str]:
    """
    Issues a new ballot to a given voter. The ballot number of the new ballot. This method should NOT invalidate any old
    ballots. If the voter isn't registered, should return None.

    :params: voter_national_id The sensitive ID of the voter to issue a new ballot to.
    :returns: The ballot number of the new ballot, or None if the voter isn't registered
    """
    # TODO: Implement this!
    status = get_voter_status(voter_national_id)
    if status == VoterStatus.NOT_REGISTERED:
        return None

    return generate_ballot_number(voter_national_id)


def count_ballot(ballot: Ballot, voter_national_id: str) -> BallotStatus:
    """
    Validates and counts the ballot for the given voter. If the ballot contains a sensitive comment, this method will
    appropriately redact the sensitive comment.

    This method will return the following upon the completion:
    1. BallotStatus.FRAUD_COMMITTED - If the voter has already voted
    2. BallotStatus.VOTER_BALLOT_MISMATCH - The ballot does not belong to this voter
    3. BallotStatus.INVALID_BALLOT - The ballot has been invalidated, or does not exist
    4. BallotStatus.BALLOT_COUNTED - If the ballot submitted in this request was successfully counted
    5. BallotStatus.VOTER_NOT_REGISTERED - If the voter is not registered

    :param: ballot The Ballot to count
    :param: voter_national_id The sensitive ID of the voter who the ballot corresponds to.
    :returns: The Ballot Status after the ballot has been processed.
    """

    store = VotingStore.get_instance()

    voter = store.get_voter_by_national_id(voter_national_id)
    if voter is None:
        return BallotStatus.VOTER_NOT_REGISTERED
    if voter.voted == True:
        store.fraud_voter(voter_national_id)
        return BallotStatus.FRAUD_COMMITTED

    ballot_check = bcrypt.checkpw(
        voter_national_id.encode("utf-8"), ballot.ballot_number.encode("utf-8")
    )
    if not ballot_check:
        return BallotStatus.VOTER_BALLOT_MISMATCH

    store = VotingStore.get_instance()
    ballot_check = store.is_ballot_valid(ballot.ballot_number)
    if not ballot_check:
        return BallotStatus.INVALID_BALLOT

    ballot.voter_comments = redact_free_text(ballot.voter_comments, voter)
    store.add_ballot(ballot, voter_national_id)
    return BallotStatus.BALLOT_COUNTED


def invalidate_ballot(ballot_number: str) -> bool:
    """
    Marks a ballot as invalid so that it cannot be used. This should only work on ballots that have NOT been cast. If a
    ballot has already been cast, it cannot be invalidated.

    If the ballot does not exist or has already been cast, this method will return false.

    :returns: If the ballot does not exist or has already been cast, will return Boolean FALSE.
              Otherwise will return Boolean TRUE.
    """
    store = VotingStore.get_instance()
    ballot_counted = store.is_ballot_counted(ballot_number)
    if ballot_counted:
        return False

    store.invalidate_ballot(ballot_number)
    return True


def verify_ballot(voter_national_id: str, ballot_number: str) -> bool:
    """
    Verifies the following:

    1. That the ballot was specifically issued to the voter specified
    2. That the ballot is not invalid

    If all of the points above are true, then returns Boolean True. Otherwise returns Boolean False.

    :param: voter_national_id The id of the voter about to cast the ballot with the given ballot number
    :param: ballot_number The ballot number of the ballot that is about to be cast by the given voter
    :returns: Boolean True if the ballot was issued to the voter specified, and if the ballot has not been marked as
              invalid. Boolean False otherwise.
    """
    ballot_check = bcrypt.checkpw(
        voter_national_id.encode("utf-8"), ballot_number.encode("utf-8")
    )
    if not ballot_check:
        return False

    store = VotingStore.get_instance()
    ballot_check = store.is_ballot_valid(ballot_number)
    if not ballot_check:
        return False

    return True


#
# Aggregate API
#


def get_all_ballot_comments() -> Set[str]:
    """
    Returns a list of all the ballot comments that are non-empty.
    :returns: A list of all the ballot comments that are non-empty
    """
    # TODO: Implement this!
    store = VotingStore.get_instance()
    return store.get_all_non_empty_ballot_comments()


def compute_election_winner() -> Candidate:
    """
    Computes the winner of the election - the candidate that gets the most votes (even if there is not a majority).
    :return: The winning Candidate
    """
    store = VotingStore.get_instance()
    return store.get_top_candidate()


def get_all_fraudulent_voters() -> Set[str]:
    """
    Returns a complete list of voters who committed fraud. For example, if the following committed fraud:

    1. first: "John", last: "Smith"
    2. first: "Linda", last: "Navarro"

    Then this method would return {"John Smith", "Linda Navarro"} - with a space separating the first and last names.
    """
    # TODO: Implement this!
    store = VotingStore.get_instance()
    fraud_voters = store.get_fraud_voters()
    result = set()

    for voter in fraud_voters:
        first_name = decrypt_name(voter.first_name)
        last_name = decrypt_name(voter.last_name)
        result.add(first_name + " " + last_name)

    return result
