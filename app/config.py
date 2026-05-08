from __future__ import annotations

from configparser import ConfigParser
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os
import re


def _load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _as_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_wallet_dir(raw_value: str, repo_root: Path) -> str:
    value = raw_value.strip()
    if not value:
        return ""

    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return str(candidate)

    repo_relative = (repo_root / candidate).resolve()
    if repo_relative.exists():
        return str(repo_relative)

    terraform_relative = (repo_root / "features" / "agent_memory" / "infra" / "terraform" / candidate).resolve()
    return str(terraform_relative)


def _resolve_db_dsn(raw_dsn: str, wallet_dir: str) -> str:
    dsn = raw_dsn.strip()
    if not dsn or not wallet_dir:
        return dsn

    tnsnames_path = Path(wallet_dir) / "tnsnames.ora"
    if not tnsnames_path.exists():
        return dsn

    if "/" not in dsn:
        return dsn

    service_name = dsn.split("/", 1)[1].strip()
    if not service_name:
        return dsn

    tnsnames_text = tnsnames_path.read_text(encoding="utf-8")
    for raw_line in tnsnames_text.splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        alias, descriptor = line.split("=", 1)
        if service_name in descriptor:
            return alias.strip()

    return dsn


def _load_oci_profile(profile_name: str) -> dict[str, str]:
    config_path = Path("~/.oci/config").expanduser()
    if not config_path.exists():
        return {}

    parser = ConfigParser()
    parser.read(config_path, encoding="utf-8")
    if profile_name == parser.default_section:
        section = parser.defaults()
    elif parser.has_section(profile_name):
        section = parser[profile_name]
    else:
        return {}

    key_file = section.get("key_file", "").strip()
    if key_file:
        key_file = str(Path(key_file).expanduser())

    return {
        "user": section.get("user", "").strip(),
        "fingerprint": section.get("fingerprint", "").strip(),
        "tenancy": section.get("tenancy", "").strip(),
        "region": section.get("region", "").strip(),
        "key_file": key_file,
    }


def _load_compartment_ocid(repo_root: Path) -> str:
    explicit = os.getenv("OCI_COMPARTMENT_OCID", "").strip() or os.getenv("TF_VAR_compartment_ocid", "").strip()
    if explicit:
        return explicit

    tfvars_path = repo_root / "features" / "agent_memory" / "infra" / "terraform" / "terraform.tfvars"
    if not tfvars_path.exists():
        return ""

    match = re.search(
        r'^\s*compartment_ocid\s*=\s*"([^"]+)"',
        tfvars_path.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else ""


@dataclass(frozen=True)
class Settings:
    app_name: str
    demo_username: str
    demo_password: str
    agent_memory_mode: str
    agent_memory_schema_policy: str
    oci_cli_profile: str
    oci_compartment_ocid: str
    oci_genai_region: str
    oci_genai_project_ocid: str
    oci_genai_api_key: str
    oci_genai_chat_model: str
    oci_native_user: str
    oci_native_fingerprint: str
    oci_native_tenancy: str
    oci_native_key_file: str
    oci_native_region: str
    agent_memory_db_user: str
    agent_memory_db_password: str
    agent_memory_db_dsn: str
    agent_memory_wallet_dir: str
    agent_memory_wallet_password: str
    agent_memory_llm_model: str
    agent_memory_embedding_model: str
    repo_root: Path

    @property
    def static_dir(self) -> Path:
        return self.repo_root / "app" / "static"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    repo_root = Path(__file__).resolve().parents[1]
    _load_env_file(repo_root / ".env")
    oci_cli_profile = os.getenv("OCI_CLI_PROFILE", "DEFAULT").strip() or "DEFAULT"
    oci_profile = _load_oci_profile(oci_cli_profile)

    return Settings(
        app_name=os.getenv("APP_NAME", "Enterprise AI Feature Studio"),
        demo_username=os.getenv("APP_DEMO_USERNAME", "oci").strip() or "oci",
        demo_password=os.getenv("APP_DEMO_PASSWORD", "").strip(),
        agent_memory_mode=os.getenv("AGENT_MEMORY_MODE", "live").strip().lower() or "live",
        agent_memory_schema_policy=os.getenv("AGENT_MEMORY_SCHEMA_POLICY", "create_if_necessary").strip().lower() or "create_if_necessary",
        oci_cli_profile=oci_cli_profile,
        oci_compartment_ocid=_load_compartment_ocid(repo_root),
        oci_genai_region=os.getenv("OCI_GENAI_REGION", "us-chicago-1"),
        oci_genai_project_ocid=os.getenv("OCI_GENAI_PROJECT_OCID", ""),
        oci_genai_api_key=os.getenv("OCI_GENAI_API_KEY", ""),
        oci_genai_chat_model=os.getenv("OCI_GENAI_CHAT_MODEL", "openai.gpt-oss-120b"),
        oci_native_user=os.getenv("OCI_USER", "").strip() or oci_profile.get("user", ""),
        oci_native_fingerprint=os.getenv("OCI_FINGERPRINT", "").strip() or oci_profile.get("fingerprint", ""),
        oci_native_tenancy=os.getenv("OCI_TENANCY", "").strip() or oci_profile.get("tenancy", ""),
        oci_native_key_file=str(Path(os.getenv("OCI_KEY_FILE", "").strip()).expanduser()) if os.getenv("OCI_KEY_FILE", "").strip() else oci_profile.get("key_file", ""),
        oci_native_region=os.getenv("OCI_REGION", "").strip() or oci_profile.get("region", "") or os.getenv("OCI_GENAI_REGION", "us-chicago-1"),
        agent_memory_db_user=os.getenv("AGENT_MEMORY_DB_USER", ""),
        agent_memory_db_password=os.getenv("AGENT_MEMORY_DB_PASSWORD", ""),
        agent_memory_db_dsn=_resolve_db_dsn(
            os.getenv("AGENT_MEMORY_DB_DSN", ""),
            _resolve_wallet_dir(
                os.getenv("AGENT_MEMORY_WALLET_DIR", ""),
                repo_root,
            ),
        ),
        agent_memory_wallet_dir=_resolve_wallet_dir(
            os.getenv("AGENT_MEMORY_WALLET_DIR", ""),
            repo_root,
        ),
        agent_memory_wallet_password=os.getenv("AGENT_MEMORY_WALLET_PASSWORD", ""),
        agent_memory_llm_model=os.getenv(
            "AGENT_MEMORY_LLM_MODEL",
            "oci/cohere.command-latest",
        ),
        agent_memory_embedding_model=os.getenv(
            "AGENT_MEMORY_EMBEDDING_MODEL",
            "oci/cohere.embed-v4.0",
        ),
        repo_root=repo_root,
    )
