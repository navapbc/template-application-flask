"""Bulk database operations for performance.

Provides a bulk_upsert function for use with
Postgres and the psycopg library.
"""
from typing import Any, Sequence

import psycopg
from psycopg import rows, sql

Connection = psycopg.Connection
Cursor = psycopg.Cursor
kwargs_row = rows.kwargs_row


def bulk_upsert(
    cur: psycopg.Cursor,
    table: str,
    attributes: Sequence[str],
    objects: Sequence[Any],
    constraint: str,
    update_condition: sql.SQL | None = None,
) -> None:
    """Bulk insert or update a sequence of objects.

    Insert a sequence of objects, or update on conflict.
    Write data from one table to another.
    If there are conflicts due to unique constraints, overwrite existing data.

    Args:
      cur: the Cursor object from the pyscopg library
      table: the name of the table to insert into or update
      attributes: a sequence of attribute names to copy from each object
      objects: a sequence of objects to upsert
      constraint: the table unique constraint to use to determine conflicts
      update_condition: optional WHERE clause to limit updates for a
        conflicting row
    """
    if not update_condition:
        update_condition = sql.SQL("")

    temp_table = f"temp_{table}"
    _create_temp_table(cur, temp_table=temp_table, src_table=table)
    _bulk_insert(cur, table=temp_table, columns=attributes, objects=objects)
    _write_from_table_to_table(
        cur,
        src_table=temp_table,
        dest_table=table,
        columns=attributes,
        constraint=constraint,
        update_condition=update_condition,
    )


def _create_temp_table(cur: psycopg.Cursor, temp_table: str, src_table: str) -> None:
    """
    Create table that lives only for the current transaction.
    Use an existing table to determine the table structure.
    Once the transaction is committed the temp table will be deleted.
    Args:
      temp_table: the name of the temporary table to create
      src_table: the name of the existing table
    """
    cur.execute(
        sql.SQL(
            "CREATE TEMP TABLE {temp_table}\
      (LIKE {src_table})\
      ON COMMIT DROP"
        ).format(
            temp_table=sql.Identifier(temp_table),
            src_table=sql.Identifier(src_table),
        )
    )


def _bulk_insert(
    cur: psycopg.Cursor,
    table: str,
    columns: Sequence[str],
    objects: Sequence[Any],
) -> None:
    """
    Write data from a sequence of objects to a temp table.
    This function uses the PostgreSQL COPY command which is highly performant.
    Args:
      cur: the Cursor object from the pyscopg library
      table: the name of the temporary table
      columns: a sequence of column names that are attributes of each object
      objects: a sequence of objects with attributes defined by columns
    """
    columns_sql = sql.SQL(",").join(map(sql.Identifier, columns))
    query = sql.SQL("COPY {table}({columns}) FROM STDIN").format(
        table=sql.Identifier(table),
        columns=columns_sql,
    )
    with cur.copy(query) as copy:
        for obj in objects:
            values = [getattr(obj, column) for column in columns]
            copy.write_row(values)


def _write_from_table_to_table(
    cur: psycopg.Cursor,
    src_table: str,
    dest_table: str,
    columns: Sequence[str],
    constraint: str,
    update_condition: sql.SQL | None = None,
) -> None:
    """
    Write data from one table to another.
    If there are conflicts due to unique constraints, overwrite existing data.
    Args:
      cur: the Cursor object from the pyscopg library
      src_table: the name of the table that will be copied from
      dest_table: the name of the table that will be written to
      columns: a sequence of column names to copy over
      constraint: the arbiter constraint to use to determine conflicts
      update_condition: optional WHERE clause to limit updates for a
        conflicting row
    """
    if not update_condition:
        update_condition = sql.SQL("")

    columns_sql = sql.SQL(",").join(map(sql.Identifier, columns))
    update_sql = sql.SQL(",").join(
        [
            sql.SQL("{column} = EXCLUDED.{column}").format(
                column=sql.Identifier(column),
            )
            for column in columns
            if column not in ["id", "number"]
        ]
    )
    query = sql.SQL(
        "INSERT INTO {dest_table}({columns})\
    SELECT {columns} FROM {src_table}\
    ON CONFLICT ON CONSTRAINT {constraint} DO UPDATE SET {update_sql}\
      {update_condition}"
    ).format(
        dest_table=sql.Identifier(dest_table),
        columns=columns_sql,
        src_table=sql.Identifier(src_table),
        constraint=sql.Identifier(constraint),
        update_sql=update_sql,
        update_condition=update_condition,
    )
    cur.execute(query)


__all__ = ["bulk_upsert"]
