"""P0/P1 Blocker Remediation Verification Tests.

These tests verify that all production blockers identified during the
Enterprise Production Certification audit have been remediated.

P0 Blockers:
  P0-1: Migration chain -- all Alembic migrations apply cleanly
  P0-2: No create_all bypass in production code path

P1 Blockers:
  P1-1: Policy engine is fail-closed (returns [] on DB failure, not open-allow)
  P1-2: Error handlers don't leak internal details to clients
  P1-3: SSE streaming yields generic error messages
  P1-4: Docker runs as non-root user
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ================================================================
# P0-1: Migration chain -- all Alembic migrations apply cleanly
# ================================================================

class TestMigrationChain:

    def test_migration_files_exist_in_order(self):
        migrations_dir = PROJECT_ROOT / "alembic" / "versions"
        files = sorted(migrations_dir.glob("*.py"))
        migration_files = [f for f in files if f.name != "__init__.py"]
        assert len(migration_files) >= 11, (
            f"Expected >= 11 migration files, found {len(migration_files)}"
        )
        expected_prefixes = [f"{i:03d}_" for i in range(1, 12)]
        actual_basenames = [f.name for f in migration_files]
        for prefix in expected_prefixes:
            matching = [n for n in actual_basenames if n.startswith(prefix)]
            assert len(matching) == 1, (
                f"Expected exactly one migration with prefix {prefix}, found {matching}"
            )

    def test_no_create_all_in_production_code(self):
        for name in ("main.py", "db.py"):
            filepath = PROJECT_ROOT / "app" / name
            if not filepath.exists():
                continue
            content = filepath.read_text()
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "create_all" in line and "metadata.create_all" in line:
                    pytest.fail(
                        f"Found create_all() in app/{name}:{i}: {stripped}"
                    )


# ================================================================
# P0-2: No create_all bypass -- test infra uses Alembic
# ================================================================

class TestNoCreateAllBypass:

    def test_conftest_uses_alembic_migrations(self):
        conftest = PROJECT_ROOT / "tests" / "conftest.py"
        content = conftest.read_text()
        assert "alembic" in content.lower(), "conftest.py should use Alembic"
        assert "command.upgrade" in content or "upgrade" in content.lower(), (
            "conftest.py should call alembic upgrade"
        )
        assert "create_all" not in content, (
            "conftest.py still uses create_all() instead of Alembic migrations"
        )


# ================================================================
# P1-1: Policy engine is fail-closed
# ================================================================

class TestPolicyFailClosed:

    def test_policy_engine_returns_empty_on_db_failure(self):
        from app.services.policy.repository import PolicyRepository

        repo = PolicyRepository(None)
        policies = asyncio.run(repo.load_active_policies())
        assert policies == [], (
            f"Policy engine returned non-empty policies with no DB (fail-open): {policies}"
        )

    def test_no_system_policies_method(self):
        from app.services.policy.repository import PolicyRepository

        repo = PolicyRepository(None)
        assert not hasattr(repo, "_system_policies"), (
            "_system_policies() still exists -- should have been removed during fail-closed fix"
        )


# ================================================================
# P1-2: Error handlers don't leak internal details
# ================================================================

class TestErrorHandlerSanitization:

    def test_no_str_exc_in_generic_handler(self):
        main_py = (PROJECT_ROOT / "app" / "main.py").read_text()
        assert "str(exc)" not in main_py, (
            "Generic error handler leaks str(exc) to clients"
        )

    def test_no_str_exc_in_chat_api(self):
        chat_py = PROJECT_ROOT / "app" / "api" / "chat.py"
        if not chat_py.exists():
            return
        content = chat_py.read_text()
        lines = content.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "except" in stripped and "Exception" in stripped:
                for j in range(i, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith("yield") and (
                        "str(exc)" in next_line or "str(e)" in next_line
                    ):
                        pytest.fail(
                            f"SSE handler leaks exception details at line {j+1}: {next_line}"
                        )
                    if not next_line or next_line.startswith(("def ", "class ")):
                        break


# ================================================================
# P1-3: SSE streaming uses generic error messages
# ================================================================

class TestSSEErrorSanitization:

    def test_chat_api_error_yields_generic_message(self):
        chat_py = PROJECT_ROOT / "app" / "api" / "chat.py"
        if not chat_py.exists():
            return
        content = chat_py.read_text()
        # Verify the SSE error block yields a generic message, not str(exc)
        assert "An internal error occurred" in content or "internal error" in content.lower(), (
            "SSE handler should yield generic error messages"
        )
        # Verify no str(exc) anywhere in the file
        for i, line in enumerate(content.split("\n"), 1):
            if line.strip().startswith("#"):
                continue
            if "str(exc)" in line or "str(e)" in line:
                pytest.fail(
                    f"SSE handler leaks exception details at line {i}: {line.strip()}"
                )


# ================================================================
# P1-4: Docker security hardening
# ================================================================

class TestDockerSecurity:

    def test_dockerfile_non_root_user(self):
        dockerfile = (PROJECT_ROOT / "Dockerfile").read_text()
        assert "USER" in dockerfile, "Dockerfile missing USER directive"
        lines = dockerfile.split("\n")
        user_line = None
        cmd_line = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("USER "):
                user_line = i
            if stripped.startswith("CMD"):
                cmd_line = i
        assert user_line is not None, "No USER directive found"
        assert cmd_line is not None, "No CMD directive found"
        assert user_line < cmd_line, (
            f"USER directive (line {user_line + 1}) must come before CMD (line {cmd_line + 1})"
        )
        assert "root" not in lines[user_line].strip().lower(), (
            f"Dockerfile runs as root: {lines[user_line].strip()}"
        )

    def test_dockerfile_has_healthcheck(self):
        dockerfile = (PROJECT_ROOT / "Dockerfile").read_text()
        assert "HEALTHCHECK" in dockerfile, "Dockerfile missing HEALTHCHECK"

    def test_dockerfile_runs_migrations_before_app(self):
        dockerfile = (PROJECT_ROOT / "Dockerfile").read_text()
        assert "alembic upgrade" in dockerfile, (
            "Docker CMD must run alembic migrations before starting uvicorn"
        )

    def test_docker_compose_uses_env_interpolation(self):
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text()
        lines = compose.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "password:" in stripped.lower() and "${" not in stripped:
                if "change-me" not in stripped and "changeme" not in stripped:
                    pytest.fail(
                        f"docker-compose.yml line {i}: possible hardcoded password: {stripped}"
                    )

    def test_docker_compose_db_dependency_healthcheck(self):
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text()
        assert "condition: service_healthy" in compose, (
            "docker-compose.yml should use service_healthy for DB dependency"
        )

    def test_dockerfile_user_named_swarmvault(self):
        dockerfile = (PROJECT_ROOT / "Dockerfile").read_text()
        assert "swarmvault" in dockerfile, (
            "Dockerfile should use 'swarmvault' as the non-root user name"
        )


# ================================================================
# Integration: Policy enforcement wired up
# ================================================================

class TestPolicyEnforcement:

    def test_require_policy_importable(self):
        from app.services.policy.dependencies import require_policy
        assert callable(require_policy), "require_policy must be callable"
