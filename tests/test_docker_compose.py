from pathlib import Path

import pytest
import yaml

HERE = Path(__file__).resolve().parent.parent
COMPOSE = HERE / "docker-compose.yml"
DOCKERFILE = HERE / "Dockerfile"
GATEWAY_DOCKERFILE = HERE / "whatsapp-gateway" / "Dockerfile"


def test_compose_file_exists():
    assert COMPOSE.exists(), "docker-compose.yml not found"


def test_compose_valid_yaml():
    with open(COMPOSE) as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), "docker-compose.yml must be a mapping"
    assert "services" in data, "docker-compose.yml must have 'services' key"


def test_compose_required_services():
    with open(COMPOSE) as f:
        services = yaml.safe_load(f)["services"]
    required = {"api", "whatsapp-gateway", "db", "redis"}
    assert required.issubset(services), f"Missing services: {required - set(services)}"


def test_api_service():
    with open(COMPOSE) as f:
        svc = yaml.safe_load(f)["services"]["api"]
    assert svc.get("build") == ".", "api: build path must be '.'"
    assert "8000:8000" in svc.get("ports", []), "api: missing port 8000"
    assert "db" in svc.get("depends_on", {}), "api: missing db dependency"
    deps = list(svc.get("depends_on", {}).keys())
    assert "redis" in deps, "api: missing redis dependency"
    assert "whatsapp-gateway" in deps, "api: missing whatsapp-gateway dependency"


def test_whatsapp_gateway_service():
    with open(COMPOSE) as f:
        svc = yaml.safe_load(f)["services"]["whatsapp-gateway"]
    assert svc.get("build") == "./whatsapp-gateway", "build path must be ./whatsapp-gateway"
    assert "3000:3000" in svc.get("ports", []), "missing port 3000"
    vols = svc.get("volumes", [])
    assert any("whatsapp-session" in v for v in vols), "missing whatsapp-session volume"


def test_db_service():
    with open(COMPOSE) as f:
        svc = yaml.safe_load(f)["services"]["db"]
    assert "postgres:16" in svc.get("image", ""), "db: image must be postgres:16-alpine"
    assert "5432:5432" in svc.get("ports", []), "db: missing port 5432"
    vols = svc.get("volumes", [])
    assert any("pgdata" in v for v in vols), "db: missing pgdata volume"
    assert "healthcheck" in svc, "db: missing healthcheck"


def test_redis_service():
    with open(COMPOSE) as f:
        svc = yaml.safe_load(f)["services"]["redis"]
    assert "redis:7" in svc.get("image", ""), "redis: image must be redis:7-alpine"
    assert "6379:6379" in svc.get("ports", []), "redis: missing port 6379"


def test_compose_volumes():
    with open(COMPOSE) as f:
        volumes = yaml.safe_load(f).get("volumes", {})
    assert "pgdata" in volumes, "missing pgdata volume definition"
    assert "whatsapp-session" in volumes, "missing whatsapp-session volume definition"


@pytest.mark.parametrize("file,label", [
    (DOCKERFILE, "api"),
    (GATEWAY_DOCKERFILE, "whatsapp-gateway"),
])
def test_dockerfiles_exist(file, label):
    assert file.exists(), f"{label} Dockerfile not found at {file}"
    content = file.read_text()
    assert "FROM" in content, f"{label}: missing FROM instruction"
    assert len(content.strip()) > 20, f"{label}: Dockerfile too short"


def test_dockerfile_api():
    content = DOCKERFILE.read_text()
    assert "python" in content.lower() or "python" in content, "api: must use Python base image"
    assert "8000" in content or "uvicorn" in content, "api: missing port or uvicorn"


def test_dockerfile_gateway():
    content = GATEWAY_DOCKERFILE.read_text()
    assert "node" in content.lower() or "node" in content, "gateway: must use Node base image"
    assert "3000" in content or "npm" in content or "index.js" in content, "gateway: missing port or entrypoint"
