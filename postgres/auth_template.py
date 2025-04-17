# AUTH details for Postgres

import psycopg2

# FIXME: Copy this and fill in your auth details for postgres. Name the copy 'auth.py'

class Auth:
    DBNAME = ''
    USERNAME = ''
    HOSTNAME = 'localhost'
    PORT = '5432'

    @classmethod
    def get_db_conn(cls):
        """Connects to PostgreSQL DB."""
        try:
            return psycopg2.connect(
                dbname=cls.DBNAME,
                user=cls.USER,
                host=cls.HOST,
                port=cls.PORT
            )
        except psycopg2.OperationalError as e:
            raise RuntimeError("Postgres connection failed") from e