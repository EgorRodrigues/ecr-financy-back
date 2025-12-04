from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra import ConsistencyLevel
from cassandra.query import SimpleStatement
from typing import Optional


def _consistency_from_str(level: str) -> ConsistencyLevel:
    lookup = {
        "ANY": ConsistencyLevel.ANY,
        "ONE": ConsistencyLevel.ONE,
        "TWO": ConsistencyLevel.TWO,
        "THREE": ConsistencyLevel.THREE,
        "QUORUM": ConsistencyLevel.QUORUM,
        "ALL": ConsistencyLevel.ALL,
        "LOCAL_QUORUM": ConsistencyLevel.LOCAL_QUORUM,
        "EACH_QUORUM": ConsistencyLevel.EACH_QUORUM,
        "LOCAL_ONE": ConsistencyLevel.LOCAL_ONE,
    }
    return lookup.get(level.upper(), ConsistencyLevel.LOCAL_QUORUM)


def connect_cassandra(settings):
    auth: Optional[PlainTextAuthProvider] = None
    if settings.cassandra_username and settings.cassandra_password:
        auth = PlainTextAuthProvider(settings.cassandra_username, settings.cassandra_password)
    cluster = Cluster(contact_points=settings.cassandra_hosts, port=settings.cassandra_port, auth_provider=auth)
    session = cluster.connect()
    _ensure_keyspace(session, settings.cassandra_keyspace)
    session.set_keyspace(settings.cassandra_keyspace)
    _ensure_tables(session)
    return session


def close_cassandra(session):
    if session:
        session.shutdown()


def _ensure_keyspace(session, keyspace: str):
    cql = f"""
    CREATE KEYSPACE IF NOT EXISTS {keyspace}
    WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
    AND durable_writes = true;
    """
    session.execute(cql)


def _ensure_tables(session):
    transactions = """
    CREATE TABLE IF NOT EXISTS transactions (
        user_id uuid,
        id timeuuid,
        amount bigint,
        description text,
        created_at timestamp,
        PRIMARY KEY ((user_id), id)
    ) WITH CLUSTERING ORDER BY (id DESC);
    """
    session.execute(transactions)

    categories = """
    CREATE TABLE IF NOT EXISTS categories (
        user_id uuid,
        id timeuuid,
        name text,
        description text,
        created_at timestamp,
        updated_at timestamp,
        PRIMARY KEY ((user_id), id)
    ) WITH CLUSTERING ORDER BY (id DESC);
    """
    session.execute(categories)

    subcategories = """
    CREATE TABLE IF NOT EXISTS subcategories (
        user_id uuid,
        category_id timeuuid,
        id timeuuid,
        name text,
        description text,
        created_at timestamp,
        updated_at timestamp,
        PRIMARY KEY ((user_id, category_id), id)
    ) WITH CLUSTERING ORDER BY (id DESC);
    """
    session.execute(subcategories)

    cost_centers = """
    CREATE TABLE IF NOT EXISTS cost_centers (
        user_id uuid,
        id timeuuid,
        name text,
        description text,
        created_at timestamp,
        updated_at timestamp,
        PRIMARY KEY ((user_id), id)
    ) WITH CLUSTERING ORDER BY (id DESC);
    """
    session.execute(cost_centers)


def ping(session) -> bool:
    try:
        stmt = SimpleStatement("SELECT key FROM system.local", consistency_level=ConsistencyLevel.LOCAL_ONE)
        session.execute(stmt)
        return True
    except Exception:
        return False
