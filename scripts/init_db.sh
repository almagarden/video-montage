#!/bin/bash

# Create alembic migrations directory
mkdir -p alembic/versions

# Initialize alembic
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Run migrations
alembic upgrade head 