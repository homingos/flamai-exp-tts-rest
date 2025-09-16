# /src/utils/config/settings.py

import os
from typing import Any, Dict, Optional
from pathlib import Path
import yaml

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