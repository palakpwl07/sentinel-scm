"""Neo4j driver singleton with connection pooling."""

import threading

from neo4j import GraphDatabase

import config


class Neo4jClient:
    """Singleton wrapper around the Neo4j driver."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._driver = GraphDatabase.driver(
                        config.NEO4J_URI,
                        auth=(config.NEO4J_USERNAME, config.NEO4J_PASSWORD),
                        max_connection_pool_size=50,
                        connection_acquisition_timeout=30.0,
                    )
                    cls._instance = instance
        return cls._instance

    @property
    def driver(self):
        return self._driver

    def run_query(self, cypher: str, params: dict | None = None) -> list[dict]:
        """Execute a Cypher query and return records as a list of dicts."""
        with self._driver.session() as session:
            result = session.run(cypher, params or {})
            return [record.data() for record in result]

    def run_write(self, cypher: str, params: dict | None = None) -> None:
        """Execute a write query inside a managed transaction."""
        with self._driver.session() as session:
            session.execute_write(lambda tx: tx.run(cypher, params or {}).consume())

    def verify_connectivity(self) -> bool:
        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    def close(self):
        if self._driver is not None:
            self._driver.close()
            Neo4jClient._instance = None


def get_client() -> Neo4jClient:
    return Neo4jClient()
