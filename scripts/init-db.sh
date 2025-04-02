#!/bin/bash

set -e

# Function to create database and grant privileges
create_database() {
    local database=$1
    echo "Creating database '$database'"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
        DROP DATABASE IF EXISTS $database;
        CREATE DATABASE $database;
        GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;
EOSQL
}

# Create main database
echo "Creating main database: $POSTGRES_DB"
create_database $POSTGRES_DB

# Create test database if POSTGRES_MULTIPLE_DATABASES is set
if [ "$POSTGRES_MULTIPLE_DATABASES" != "" ]; then
    echo "Multiple databases requested: $POSTGRES_MULTIPLE_DATABASES"
    for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        create_database $db
    done
    echo "Multiple databases created"
fi 