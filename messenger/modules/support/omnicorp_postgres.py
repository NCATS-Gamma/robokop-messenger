"""Omnicorp service module."""
import datetime
import os
import logging
import psycopg2
from messenger.shared.util import get_curie_prefix

logger = logging.getLogger(__name__)


class OmniCorp():
    """Omnicorp service object."""

    def __init__(self):
        """Create and omnicorp service object."""
        db = 'omnicorp'
        user = 'murphy'
        port = 5432
        host = 'localhost'
        password = 'pword'
        self.prefixes = set([
            'UBERON',
            'BSPO',
            'PATO',
            'GO',
            'MONDO',
            'HP',
            'ENVO',
            'OBI',
            'CL',
            'SO',
            'CHEBI',
            'HGNC',
            'MESH'])
        logger.info("Opening Connection to ROBOKOPDB Postgres")
        self.conn = psycopg2.connect(
            dbname=db,
            user=user,
            host=host,
            port=port,
            password=password)
        self.nsingle = 0
        self.total_single_call = datetime.timedelta()
        self.npair = 0
        self.total_pair_call = datetime.timedelta()

    def __del__(self):
        """Close postgres database connection on deletion."""
        self.conn.close()

    def close(self):
        """Close postgres database connection."""
        self.conn.close()

    def get_shared_pmids_count(self, node1, node2):
        """Get shared PMIDs."""
        prefix1 = get_curie_prefix(node1)
        prefix2 = get_curie_prefix(node2)
        if (
                prefix1 not in self.prefixes or
                prefix2 not in self.prefixes
        ):
            return 0
        cur = self.conn.cursor()
        statement = f"SELECT COUNT(a.pubmedid)\n" + \
                    f"FROM omnicorp.{prefix1} a\n" + \
                    f"JOIN omnicorp.{prefix2} b ON a.pubmedid = b.pubmedid\n" + \
                    f"WHERE a.curie = %s\n" + \
                    f"AND b.curie = %s"
        try:
            cur.execute(statement, (node1, node2))
            pmid_count = cur.fetchall()[0][0]
            cur.close()
        except psycopg2.ProgrammingError as err:
            self.conn.rollback()
            cur.close()
            logger.debug('OmniCorp query error: %s\nReturning 0.', str(err))
            pmid_count = 0
        if pmid_count is None:
            logger.error("OmniCorp gave up")
            return None
        return pmid_count

    def count_pmids(self, node):
        """Count PMIDs and return result."""
        if get_curie_prefix(node) not in self.prefixes:
            return 0
        prefix = get_curie_prefix(node)
        start = datetime.datetime.now()
        cur = self.conn.cursor()
        statement = f"SELECT COUNT(pubmedid) from omnicorp.{prefix}\n" + \
                    "WHERE curie = %s"
        try:
            cur.execute(statement, (node,))
            n = cur.fetchall()[0][0]
            cur.close()
            end = datetime.datetime.now()
            self.total_single_call += (end - start)
            # logger.debug(f"""Found {n} pmids in {end-start}
            #             Total {self.total_single_call}""")
            self.nsingle += 1
            if self.nsingle % 100 == 0:
                logger.info(f"NCalls: {self.nsingle}\n" +
                            f"Total time: {self.total_single_call}\n" +
                            f"Avg Time: {self.total_single_call/self.nsingle}")
            return n
        except psycopg2.ProgrammingError as err:
            self.conn.rollback()
            cur.close()
            logger.debug('OmniCorp query error: %s\nReturning 0.', str(err))
            return 0
