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
        id timeuuid,
        amount bigint,
        description text,
        created_at timestamp,
        active boolean,
        PRIMARY KEY (id)
    );
    """
    session.execute(transactions)
    try:
        session.execute("ALTER TABLE transactions ADD active boolean")
    except Exception:
        pass

    categories = """
    CREATE TABLE IF NOT EXISTS categories (
        id timeuuid,
        name text,
        description text,
        created_at timestamp,
        updated_at timestamp,
        active boolean,
        PRIMARY KEY (id)
    );
    """
    session.execute(categories)
    try:
        session.execute("ALTER TABLE categories ADD active boolean")
    except Exception:
        pass

    subcategories = """
    CREATE TABLE IF NOT EXISTS subcategories (
        category_id timeuuid,
        id timeuuid,
        name text,
        description text,
        created_at timestamp,
        updated_at timestamp,
        active boolean,
        PRIMARY KEY ((category_id), id)
    ) WITH CLUSTERING ORDER BY (id DESC);
    """
    session.execute(subcategories)
    try:
        session.execute("ALTER TABLE subcategories ADD active boolean")
    except Exception:
        pass

    cost_centers = """
    CREATE TABLE IF NOT EXISTS cost_centers (
        id timeuuid,
        name text,
        description text,
        created_at timestamp,
        updated_at timestamp,
        active boolean,
        PRIMARY KEY (id)
    );
    """
    session.execute(cost_centers)
    try:
        session.execute("ALTER TABLE cost_centers ADD active boolean")
    except Exception:
        pass

    contacts = """
    CREATE TABLE IF NOT EXISTS contacts (
        id timeuuid,
        type text,
        person_type text,
        name text,
        document text,
        email text,
        phone_e164 text,
        phone_local text,
        address text,
        notes text,
        active boolean,
        created_at timestamp,
        updated_at timestamp,
        PRIMARY KEY (id)
    );
    """
    session.execute(contacts)
    try:
        session.execute("ALTER TABLE contacts ADD active boolean")
    except Exception:
        pass
    try:
        session.execute("ALTER TABLE contacts ADD document text")
    except Exception:
        pass

    expenses = """
    CREATE TABLE IF NOT EXISTS expenses (
        id timeuuid,
        amount decimal,
        status text,
        issue_date date,
        due_date date,
        payment_date date,
        original_amount decimal,
        interest decimal,
        fine decimal,
        discount decimal,
        total_paid decimal,
        category_id text,
        subcategory_id text,
        cost_center_id text,
        contact_id text,
        description text,
        document text,
        payment_method text,
        account text,
        recurrence boolean,
        competence text,
        project text,
        tags list<text>,
        notes text,
        active boolean,
        created_at timestamp,
        updated_at timestamp,
        PRIMARY KEY (id)
    );
    """
    session.execute(expenses)
    try:
        session.execute("ALTER TABLE expenses ADD active boolean")
    except Exception:
        pass
    # Ensure newly added payment fields exist even if table already created previously
    for stmt in [
        "ALTER TABLE expenses ADD original_amount decimal",
        "ALTER TABLE expenses ADD interest decimal",
        "ALTER TABLE expenses ADD fine decimal",
        "ALTER TABLE expenses ADD discount decimal",
        "ALTER TABLE expenses ADD total_paid decimal",
    ]:
        try:
            session.execute(stmt)
        except Exception:
            pass

    incomes = """
    CREATE TABLE IF NOT EXISTS incomes (
        id timeuuid,
        amount decimal,
        status text,
        issue_date date,
        due_date date,
        receipt_date date,
        original_amount decimal,
        interest decimal,
        fine decimal,
        discount decimal,
        total_received decimal,
        category_id text,
        subcategory_id text,
        cost_center_id text,
        contact_id text,
        description text,
        document text,
        receiving_method text,
        account text,
        recurrence boolean,
        competence text,
        project text,
        tags list<text>,
        notes text,
        active boolean,
        created_at timestamp,
        updated_at timestamp,
        PRIMARY KEY (id)
    );
    """
    session.execute(incomes)
    try:
        session.execute("ALTER TABLE incomes ADD active boolean")
    except Exception:
        pass
    for stmt in [
        "ALTER TABLE incomes ADD original_amount decimal",
        "ALTER TABLE incomes ADD interest decimal",
        "ALTER TABLE incomes ADD fine decimal",
        "ALTER TABLE incomes ADD discount decimal",
        "ALTER TABLE incomes ADD total_received decimal",
    ]:
        try:
            session.execute(stmt)
        except Exception:
            pass


def ping(session) -> bool:
    try:
        stmt = SimpleStatement("SELECT key FROM system.local", consistency_level=ConsistencyLevel.LOCAL_ONE)
        session.execute(stmt)
        return True
    except Exception:
        return False
