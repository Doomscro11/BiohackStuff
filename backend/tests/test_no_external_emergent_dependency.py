"""Regression guards for removing builder-specific Emergent dependencies."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_external_emergent_dependency_not_declared():
    requirements = (REPO_ROOT / "backend" / "requirements.txt").read_text()

    assert "emergentintegrations" not in requirements


def test_emergent_builder_metadata_not_committed():
    assert not (REPO_ROOT / ".emergent" / "emergent.yml").exists()
    assert not (REPO_ROOT / ".emergent" / "summary.txt").exists()


def test_native_llm_service_exists():
    llm_service = REPO_ROOT / "backend" / "services" / "llm_service.py"
    source = llm_service.read_text()

    assert llm_service.exists()
    assert "from openai import AsyncOpenAI" in source
    assert "OPENAI_API_KEY" in source
