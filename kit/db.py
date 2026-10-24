"""The agents' database `work`, as the apps see it: read on every schema the
agents made, write only in schema `apps`. On the box an app runs as the
ygg-apps account and Postgres logs it in as the role of that name over the
local socket — no password anywhere. Elsewhere (your laptop) set
KIT_DATABASE_URL, e.g. postgresql://user:pw@host/work."""
from __future__ import annotations

import os
from contextlib import contextmanager

import pandas as pd
import psycopg

DATABASE_URL = os.environ.get("KIT_DATABASE_URL", "postgresql:///work")


@contextmanager
def connect(*, read_only: bool = True):
    """A connection, read-only by default (writes to schema `apps` need
    read_only=False). Closed on exit."""
    with psycopg.connect(DATABASE_URL, connect_timeout=5, application_name="shiny app",
                         options="-c statement_timeout=30000") as conn:
        conn.read_only = read_only
        yield conn


def query(sql: str, params=None) -> list[tuple]:
    """Rows of one statement."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall() if cur.description else []


def query_df(sql: str, params=None) -> pd.DataFrame:
    """One statement as a DataFrame, columns named as the query names them."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        if not cur.description:
            return pd.DataFrame()
        cols = [d.name for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)
