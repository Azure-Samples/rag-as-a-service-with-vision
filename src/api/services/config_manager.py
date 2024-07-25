import json
import os

from models.rag_config import RagConfig


_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "rag_configs"
)


def _build_config_path(config_id: str) -> str:
    config_path = os.path.join(_CONFIG_PATH, f"{config_id}.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"The config id {config_id} does not exist...")
    return config_path


def load_config(config_id: str):
    config_path = _build_config_path(config_id)

    file_content: dict
    with open(config_path, "r") as f:
        file_content = json.load(f)

    return RagConfig(**file_content)
