# Database Management

- [Basic operations](#basic-operations)
  - [Initialize](#initialize)
  - [Start](#start)
  - [Destroy and reinitialize](#destroy-and-reinitialize)
- [Running migrations](#running-migrations)
- [Creating new migrations](#creating-new-migrations)
- [Multi-head situations](#multi-head-situations)

## Basic operations
### Initialize

To start a local Postgres database container in a detached state and run any
pending migrations, run `make init-db`. During initial setup, `init-db` is called
automatically when running `make init`.

### Start

To only start the database container, run the following command:

```sh
make start-db
```
This command is not needed when starting the application with `make start`

### Destroy and reinitialize

To clean the database, use the following command:

```sh
make db-recreate
```

This will remove _all_ docker project volumes, rebuild the database volume, and 
run all pending migrations. Once completed, only the database container will be 
running. Simply run `make start` to bring up all other project containers.

## Running migrations

When you're first setting up your environment, ensure that migrations are run
against your db so it has all the required tables. `make init` does this, but if
needing to work with the migrations directly, some common commands:

```sh
make db-upgrade       # Apply pending migrations to db
make db-downgrade     # Rollback last migration to db
make db-downgrade-all # Rollback all migrations
```

## Creating new migrations

If you've changed a python object model, auto-generate a migration file for the database and run it:

```sh
$ make db-migrate-create MIGRATE_MSG="<brief description of change>"
$ make db-upgrade
```

<details>
    <summary>Example: Adding a new column to an existing table:</summary>

1. Manually update the database models with the changes ([example_models.py](/app/src/db/models/example_models.py) in this example)
```python
class ExampleTable(Base):
    ...
    my_new_timestamp = Column(TIMESTAMP(timezone=True)) # Newly added line
```

2. Automatically generate a migration file with `make db-migrate-create MIGRATE_MSG="Add created_at timestamp to address table"`
```python
...
def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("example_table", sa.Column("my_new_timestamp", sa.TIMESTAMP(timezone=True), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("example_table", "my_new_timestamp")
    # ### end Alembic commands ###
```

3. Manually adjust the migration file as needed. Some changes will not fully auto-generate (like foreign keys), so make sure that all desired changes are included.
</details>

## Multi-head situations

Alembic migrations form an ordered history, with each migration having at least
one parent migration as specified by the `down_revision` variable. This can be
visualized by:

```sh
make db-migrate-history
```

When multiple migrations are created that point to the same `down_revision` a
branch is created, with the tip of each branch being a "head". The above history
command will show this, but a list of just the heads can been retrieved with:

```sh
make db-migrate-heads
```

CI/CD runs migrations to reach the "head". When there are multiple, Alembic
can't resolve which migrations need to be run. If you run into this error,
you'll need to fix the migration branches/heads before merging to `main`.

If the migrations don't depend on each other, which is likely if they've
branched, then you can just run:

``` sh
make db-migrate-merge-heads
```

Which will create a new migration pointing to all current "head"s, effectively
pulling them all together.

Or, if you wish to avoid creating extra migrations, you can manually adjust
the `down_revision` of one of the migrations to point to the other one. This
is also the necessary approach if the migrations need to happen in a defined
order.
