# scripts/run-tests.ps1
# Run the test suite against the test database.
#
# Why this exists: alembic/env.py unconditionally uses settings.database_url
# from .env, overriding the test URL that tests/conftest.py passes to Alembic.
# This script sets DATABASE_URL to the test database so migrations land there.
#
# Usage: .\scripts\run-tests.ps1 [pytest-args...]
# Example: .\scripts\run-tests.ps1 -k test_register -v

$ErrorActionPreference = 'Stop'

$env:DATABASE_URL = 'postgresql+asyncpg://swarmvault:swarmvault@localhost:5432/swarmvault_test'

$pytestArgs = @()
if ($args.Count -gt 0) {
    $pytestArgs = $args
}

Set-Location $PSScriptRoot/..
py -3.12 -m pytest @pytestArgs
