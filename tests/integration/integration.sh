#!/bin/bash

output=$(python tests/integration/my_program.py --database.port 5001)

if [ "$output" != "name='Database Application' database=DatabaseConfig(host='localhost', port=5001, user='any-db-user')" ]; then
    echo "$output does not match";
    exit 1;
fi