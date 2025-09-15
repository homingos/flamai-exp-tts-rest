import os
from dotenv import load_dotenv
from typing import Any, Dict, Optional
from pathlib import Path
import yaml
import re

# Load .env file from the project root
project_root = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=project_root / ".env")

class SettingsManager:
    _instance: Optional['SettingsManager'] = None
    _config: Optional[Dict[str, Any]] = None

    def __new__(cls) -> 'SettingsManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        config_path = Path(__file__).parent / "config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at {config_path}")
        
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
        
        # Process environment variable substitutions
        self._replace_env_vars(self._config)

    def _replace_env_vars(self, config_item: Any) -> Any:
        if isinstance(config_item, dict):
            return {k: self._replace_env_vars(v) for k, v in config_item.items()}
        elif isinstance(config_item, list):
            return [self._replace_env_vars(i) for i in config_item]
        elif isinstance(config_item, str):
            # Regex to find ${VAR_NAME} or ${VAR_NAME:default}
            match = re.match(r'^\$\{(.+?)(?::-([^}]+))?\}$', config_item)
            if match:
                var_name, default_val = match.groups()
                return os.getenv(var_name, default_val if default_val is not None else config_item)
        return config_item

    def get(self, key: str, default: Any = None) -> Any:
        if self._config is None:
            return default
        
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def get_server_config(self) -> Dict[str, Any]:
        return self.get("server", {})

    def get_app_config(self) -> Dict[str, Any]:
        return self.get("app", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        return self.get("logging", {})

# Global instance
settings = SettingsManager()