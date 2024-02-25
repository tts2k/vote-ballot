#
# This file is the interface between the stores and the database
#

import sqlite3
from sqlite3 import Connection
from typing import List, Set

from main.objects.ballot import Ballot
from main.objects.candidate import Candidate
from main.objects.voter import MinimalVoter, Voter, obfuscate_national_id


class VotingStore:
    """
    A singleton class that encapsulates the interface between the stores and the databases.

    To use, simply do:

    >>> voting_store = VotingStore.get_instance()   # this will create the stores, if they haven't been created
    >>> voting_store.add_candidate(...)  # now, you can call methods that you need here
    """

    voting_store_instance = None

    @staticmethod
    def get_instance():
        if not VotingStore.voting_store_instance:
            VotingStore.voting_store_instance = VotingStore()

        return VotingStore.voting_store_instance

    @staticmethod
    def refresh_instance():
        """
        DO NOT MODIFY THIS METHOD
        Only to be used for testing. This will only work if the sqlite connection is :memory:
        """
        if VotingStore.voting_store_instance:
            VotingStore.voting_store_instance.connection.close()
        VotingStore.voting_store_instance = VotingStore()

    def __init__(self):
        """
        DO NOT MODIFY THIS METHOD
        DO NOT call this method directly - instead use the VotingStore.get_instance method above.
        """
        self.connection = VotingStore._get_sqlite_connection()
        self.create_tables()

    @staticmethod
    def _get_sqlite_connection() -> Connection:
        """
        DO NOT MODIFY THIS METHOD
        """
        return sqlite3.connect(":memory:", check_same_thread=False)

    def create_tables(self):
        """
        Creates Tables
        """
        self.connection.execute(
            """CREATE TABLE candidates (candidate_id integer primary key autoincrement, name text)"""
        )
        self.connection.execute(
            """CREATE TABLE voters (
                voter_id integer primary key autoincrement,
                first_name text,
                last_name text,
                national_id text,
                voted bool,
                fraud_commited bool
            )"""
        )
        self.connection.execute(
            """CREATE TABLE ballots (
                ballot_number text primary key,
                candidate_id text,
                comment text,
                FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
            )"""
        )
        self.connection.execute(
            """CREATE TABLE invalid_ballots (ballot_number text primary key)"""
        )
        self.connection.commit()

    def add_candidate(self, candidate_name: str):
        """
        Adds a candidate into the candidate table, overwriting an existing entry if one exists
        """
        self.connection.execute(
            """INSERT INTO candidates (name) VALUES (?)""", (candidate_name,)
        )
        self.connection.commit()

    def get_candidate(self, candidate_id: str) -> Candidate | None:
        """
        Returns the candidate specified, if that candidate is registered. Otherwise returns None.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """SELECT * FROM candidates WHERE candidate_id=?""", (candidate_id,)
        )
        candidate_row = cursor.fetchone()
        candidate = Candidate(candidate_id, candidate_row[1]) if candidate_row else None
        self.connection.commit()

        return candidate

    def get_all_candidates(self) -> List[Candidate]:
        """
        Gets ALL the candidates from the database
        """
        cursor = self.connection.cursor()
        cursor.execute("""SELECT * FROM candidates""")
        all_candidate_rows = cursor.fetchall()
        all_candidates = [
            Candidate(str(candidate_row[0]), candidate_row[1])
            for candidate_row in all_candidate_rows
        ]
        self.connection.commit()

        return all_candidates

    def add_voter(self, voter: Voter):
        """
        Adds a voter into the voter table, overwriting an existing entry if one exists
        """
        minimal_voter = voter.get_minimal_voter()
        self.connection.execute(
            """INSERT INTO voters (first_name, last_name, national_id, fraud_commited, voted) VALUES (?, ?, ?, ?, ?)""",
            (
                minimal_voter.obfuscated_first_name,
                minimal_voter.obfuscated_last_name,
                minimal_voter.obfuscated_national_id,
                minimal_voter.fraud_commited,
                minimal_voter.voted,
            ),
        )
        self.connection.commit()

    def get_voter(self, voter_id: str) -> Voter | None:
        """
        Returns the voter specified, if that voter is registered. Otherwise returns None.
        """
        cursor = self.connection.cursor()
        cursor.execute("""SELECT * FROM voters WHERE voter_id=?""", (voter_id,))
        voter_row = cursor.fetchone()
        voter = (
            Voter(voter_row[1], voter_row[2], voter_row[3], voter_row[4], voter_row[5])
            if voter_row
            else None
        )
        self.connection.commit()

        return voter

    def fraud_voter(self, national_id):
        of_national_id = obfuscate_national_id(national_id)
        cursor = self.connection.cursor()
        cursor.execute(
            """UPDATE voters SET fraud_commited = true WHERE national_id=?""",
            (of_national_id,),
        )
        self.connection.commit()

    def get_voter_by_national_id(self, national_id: str) -> Voter | None:
        """
        Returns the voter with the national_id specified, if exists. Otherwise returns None.
        """
        of_national_id = obfuscate_national_id(national_id)
        cursor = self.connection.cursor()
        cursor.execute(
            """SELECT * FROM voters WHERE national_id=?""", (of_national_id,)
        )
        voter_row = cursor.fetchone()
        voter = (
            Voter(voter_row[1], voter_row[2], voter_row[3], voter_row[4], voter_row[5])
            if voter_row
            else None
        )
        self.connection.commit()

        return voter

    def get_all_voters(self) -> List[Voter]:
        """
        Gets ALL the voters from the database
        """
        cursor = self.connection.cursor()
        cursor.execute("""SELECT * FROM voters""")
        all_voter_rows = cursor.fetchall()
        all_voters = [
            Voter(voter_row[1], voter_row[2], voter_row[3])
            for voter_row in all_voter_rows
        ]
        self.connection.commit()

        return all_voters

    def delete_voter_by_national_id(self, national_id: str):
        """
        Delete a voter from the database by national_id
        """
        of_national_id = obfuscate_national_id(national_id)
        cursor = self.connection.cursor()
        cursor.execute("""DELETE FROM voters where national_id=?""", (of_national_id,))
        self.connection.commit()

    def add_ballot(self, ballot: Ballot, national_id: str):
        """
        Adds a voter into the voter table, overwriting an existing entry if one exists
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """INSERT INTO ballots (ballot_number, candidate_id, comment) VALUES (?, ?, ?)""",
            (
                ballot.ballot_number,
                ballot.chosen_candidate_id,
                ballot.voter_comments,
            ),
        )
        # Update voter status
        of_national_id = obfuscate_national_id(national_id)
        cursor.execute(
            """UPDATE voters SET voted = true WHERE national_id=?""", (of_national_id,)
        )
        self.connection.commit()

    def is_ballot_counted(self, ballot_number: str) -> bool:
        """
        Get ballot from a ballot number. Return None if no ballot found
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """SELECT ballot_number FROM ballots WHERE ballot_number=?""",
            (ballot_number,),
        )
        ballot_row = cursor.fetchall()
        ballot_exists = len(ballot_row) > 0
        print(len(ballot_row))
        self.connection.commit()

        return ballot_exists

    def invalidate_ballot(self, ballot_number: str):
        """
        Invalidate a ballot
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """INSERT INTO invalid_ballots (ballot_number) VALUES (?)""",
            (ballot_number,),
        )
        self.connection.commit()

    def is_ballot_valid(self, ballot_number: str) -> bool:
        """
        Check a balot for validity
        """
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM invalid_ballots WHERE ballot_number=?", (ballot_number,)
        )
        ballot_number = cursor.fetchone()

        if ballot_number is None:
            return True

        return False

    def get_top_candidate(self) -> Candidate:
        """
        Get the candidate with the most votes
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT c.candidate_id, c.name, COUNT(*) as voter_count FROM candidates c
            JOIN ballots b ON c.candidate_id = b.candidate_id
            GROUP BY c.candidate_id
            ORDER BY voter_count DESC
            """
        )
        candidate_row = cursor.fetchone()
        top_candidate = Candidate(str(candidate_row[0]), candidate_row[1])
        self.connection.commit()

        return top_candidate

    def get_all_non_empty_ballot_comments(self) -> Set[str]:
        """
        Get all ballots with non-empty comments
        """
        comment_set = set()
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT comment FROM ballots WHERE comment IS NOT NULL
            """
        )
        all_comments = cursor.fetchall()
        for comment in all_comments:
            comment_set.add(comment[0])

        self.connection.commit()

        return comment_set

    def get_fraud_voters(self) -> List[Voter]:
        """
        Get all fraud voters
        """
        fraud_voters = list()
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT first_name, last_name, national_id FROM voters WHERE fraud_commited = true
            """
        )
        all_voters = cursor.fetchall()
        for voter in all_voters:
            fraud_voters.append(Voter(voter[0], voter[1], voter[2]))

        self.connection.commit()

        return fraud_voters
