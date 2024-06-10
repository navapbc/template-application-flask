"""Tests for bulk_ops module"""
import operator
import random
from dataclasses import dataclass

from psycopg import rows, sql

import src.adapters.db as db
from src.db import bulk_ops


@dataclass
class Number:
    id: str
    num: int


def get_random_number_object() -> Number:
    return Number(
        id=str(random.randint(1000000, 9999999)),
        num=random.randint(1, 10000),
    )


def test_bulk_upsert(db_session: db.Session):
    db_client = db.PostgresDBClient()
    conn = db_client.get_raw_connection()

    # Override mypy, because SQLAlchemy's DBAPICursor type doesn't specify the row_factory attribute, or that it functions as a context manager
    with conn.cursor(row_factory=rows.class_row(Number)) as cur:  # type: ignore
        table = "temp_table"
        attributes = ["id", "num"]
        objects = [get_random_number_object() for i in range(100)]
        constraint = "temp_table_pkey"

        # Create a table for testing bulk upsert
        cur.execute(
            sql.SQL(
                "CREATE TEMP TABLE {table}"
                "("
                "id TEXT NOT NULL,"
                "num INT,"
                "CONSTRAINT {constraint} PRIMARY KEY (id)"
                ")"
            ).format(
                table=sql.Identifier(table),
                constraint=sql.Identifier(constraint),
            )
        )

        bulk_ops.bulk_upsert(
            cur,
            table,
            attributes,
            objects,
            constraint,
        )
        conn.commit()

        # Check that all the objects were inserted
        cur.execute(
            sql.SQL("SELECT id, num FROM {table} ORDER BY id ASC").format(
                table=sql.Identifier(table)
            )
        )
        records = cur.fetchall()
        objects.sort(key=operator.attrgetter("id"))
        assert records == objects

        # Now modify half of the objects
        updated_indexes = random.sample(range(100), 50)
        original_objects = [objects[i] for i in range(100) if i not in updated_indexes]
        updated_objects = [objects[i] for i in updated_indexes]
        for obj in updated_objects:
            obj.num = random.randint(1, 10000)

        # And insert additional objects
        inserted_objects = [get_random_number_object() for i in range(50)]

        updated_and_inserted_objects = updated_objects + inserted_objects
        random.shuffle(updated_objects + inserted_objects)

        bulk_ops.bulk_upsert(
            cur,
            table,
            attributes,
            updated_and_inserted_objects,
            constraint,
        )
        conn.commit()

        # Check that the existing objects were updated and new objects were inserted
        cur.execute(
            sql.SQL("SELECT id, num FROM {table} ORDER BY id ASC").format(
                table=sql.Identifier(table)
            )
        )
        records = cur.fetchall()
        expected_objects = original_objects + updated_and_inserted_objects
        expected_objects.sort(key=operator.attrgetter("id"))
        assert records == expected_objects
