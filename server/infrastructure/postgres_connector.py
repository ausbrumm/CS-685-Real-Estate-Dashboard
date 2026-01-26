import logging
from typing import Optional, Any, Iterator
import psycopg 
from psycopg import sql, Error as PostgresError
from psycopg.rows import dict_row, tuple_row
from psycopg_pool import ConnectionPool, AsyncConnectionPool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncPostgresConnector:
    """An asynchronous PostgreSQL database connector with connection pooling support."""

    # TODO: move from hardcoded defaults to environment variables
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        dbname: str = "real_estate_db",
        user: str = "postgres",
        password: str = "12345",
        use_pool: bool = True,
        min_size: int = 1,
        max_size: int = 10,
        **kwargs,
    ):
        """
        Initialize the async PostgreSQL connector.

        Args:
            host: Database server hostname
            port: Database server port
            dbname: Database name
            user: Database username
            password: Database password
            use_pool: Whether to use connection pooling
            min_size: Minimum connections in pool (if pooling enabled)
            max_size: Maximum connections in pool (if pooling enabled)
            **kwargs: Additional connection parameters
        """
        self.conninfo = psycopg.conninfo.make_conninfo(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            **kwargs,
        )
        self.use_pool = use_pool
        self.min_size = min_size
        self.max_size = max_size

        self._connection: Optional[psycopg.AsyncConnection] = None
        self._pool: Optional[AsyncConnectionPool] = None

    async def connect(self) -> None:
        """Establish an async database connection or initialize the connection pool."""
        try:
            if self.use_pool:
                self._pool = AsyncConnectionPool(
                    self.conninfo,
                    min_size=self.min_size,
                    max_size=self.max_size,
                    open=False,
                )
                await self._pool.open()
                logger.info("Async connection pool initialized successfully")
            else:
                self._connection = await psycopg.AsyncConnection.connect(self.conninfo)
                logger.info("Async connection established")
        except PostgresError as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self) -> None:
        """Close the async database connection or connection pool."""
        try:
            if self.use_pool and self._pool:
                await self._pool.close()
                self._pool = None
                logger.info("Async connection pool closed")
            elif self._connection:
                await self._connection.close()
                self._connection = None
                logger.info("Async database connection closed")
        except PostgresError as e:
            logger.error(f"Error closing connection: {e}")
            raise

    async def execute(
        self,
        query: str,
        params: Optional[tuple | dict] = None,
        returning: bool = False,
    ) -> Optional[Any]:
        """
        Execute a SQL query asynchronously.

        Args:
            query: SQL query string
            params: Query parameters
            returning: If True, return the first column of the first row

        Returns:
            Result of RETURNING clause if returning=True, else None
        """
        async with self._get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                await conn.commit()
                if returning:
                    result = await cur.fetchone()
                    return result[0] if result else None
                return None

    async def execute_many(self, query: str, params_seq: list[tuple | dict]) -> None:
        """
        Execute a SQL query multiple times with different parameters asynchronously.

        Args:
            query: SQL query string
            params_seq: Sequence of parameter tuples/dicts
        """
        async with self._get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(query, params_seq)
                await conn.commit()

    async def fetch_one(
        self,
        query: str,
        params: Optional[tuple | dict] = None,
        as_dict: bool = False,
    ) -> Optional[Any]:
        """
        Fetch a single row asynchronously.

        Args:
            query: SQL query string
            params: Query parameters
            as_dict: If True, return result as dictionary

        Returns:
            Single row result or None
        """
        row_factory = dict_row if as_dict else tuple_row
        async with self._get_connection() as conn:
            async with conn.cursor(row_factory=row_factory) as cur:
                await cur.execute(query, params)
                return await cur.fetchone()

    async def fetch_all(
        self,
        query: str,
        params: Optional[tuple | dict] = None,
        as_dict: bool = False,
    ) -> list:
        """
        Fetch all rows asynchronously.

        Args:
            query: SQL query string
            params: Query parameters
            as_dict: If True, return results as dictionaries

        Returns:
            List of row results
        """
        row_factory = dict_row if as_dict else tuple_row
        async with self._get_connection() as conn:
            async with conn.cursor(row_factory=row_factory) as cur:
                await cur.execute(query, params)
                return await cur.fetchall()

    async def fetch_many(
        self,
        query: str,
        size: int,
        params: Optional[tuple | dict] = None,
        as_dict: bool = False,
    ) -> list:
        """
        Fetch a specific number of rows asynchronously.

        Args:
            query: SQL query string
            size: Number of rows to fetch
            params: Query parameters
            as_dict: If True, return results as dictionaries

        Returns:
            List of row results (up to 'size' rows)
        """
        row_factory = dict_row if as_dict else tuple_row
        async with self._get_connection() as conn:
            async with conn.cursor(row_factory=row_factory) as cur:
                await cur.execute(query, params)
                return await cur.fetchmany(size)

    async def copy_from(
        self,
        table: str,
        data: list[tuple],
        columns: Optional[list[str]] = None,
    ) -> int:
        """
        Efficiently bulk insert data using COPY asynchronously.

        Args:
            table: Target table name
            data: List of tuples to insert
            columns: Optional list of column names

        Returns:
            Number of rows copied
        """
        col_clause = sql.SQL("({})").format(
            sql.SQL(", ").join(sql.Identifier(c) for c in columns)
        ) if columns else sql.SQL("")
        
        query = sql.SQL("COPY {} {} FROM STDIN").format(
            sql.Identifier(table),
            col_clause,
        )
        
        async with self._get_connection() as conn:
            async with conn.cursor() as cur:
                async with cur.copy(query) as copy:
                    for row in data:
                        await copy.write_row(row)
                await conn.commit()
                return len(data)

    async def table_exists(self, table_name: str, schema: str = "public") -> bool:
        """
        Check if a table exists in the database asynchronously.

        Args:
            table_name: Name of the table
            schema: Schema name (default: public)

        Returns:
            True if table exists, False otherwise
        """
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            )
        """
        result = await self.fetch_one(query, (schema, table_name))
        return result[0] if result else False

    def _get_connection(self):
        """Get a connection context manager."""
        if self.use_pool:
            if not self._pool:
                raise RuntimeError("Connection pool not initialized. Call connect() first.")
            return self._pool.connection()
        else:
            if not self._connection:
                raise RuntimeError("Not connected to database. Call connect() first.")
            return _AsyncConnectionWrapper(self._connection)

    async def __aenter__(self):
        """Async context manager entry point."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit point."""
        await self.disconnect()
        return False


class _AsyncConnectionWrapper:
    """Simple wrapper to use an existing connection as an async context manager."""
    
    def __init__(self, connection: psycopg.AsyncConnection):
        self._connection = connection
    
    async def __aenter__(self):
        return self._connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

