import pg, { QueryResult, QueryResultRow } from 'pg';

// https://node-postgres.com/

const pool = new pg.Pool({
    user: process.env.POSTGRES_USER,
    host: process.env.POSTGRES_HOST,
    database: process.env.POSTGRES_DATABASE,
    password: process.env.POSTGRES_PASSWORD || "12345",
    port: parseInt(process.env.POSTGRES_PORT || "5432"),
});

// A helper type for query parameters, this way I can use what ever type we have in our query
type QueryParam = string | number | boolean | null | undefined | Date;

// query function with generics to type the result rows
// using node-postgres's query method under the hood
export const query = <T extends QueryResultRow>(
    text: string,
    params: QueryParam[] = [],
): Promise<QueryResult<T>> => pool.query(text, params);

export default pool;
