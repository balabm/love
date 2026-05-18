"""
Project LOVE Settings Manager
Loads and manages user configuration from settings.yaml
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"
USER_CONFIG_PATH = PROJECT_ROOT / "settings.yaml"


@dataclass
class UserConfig:
    """User identity configuration."""
    name: str = "User"
    timezone: str = "UTC"
    language: str = "en"


@dataclass
class CompanionConfig:
    """AI companion personality configuration."""
    name: str = "Love"
    personality_preset: str = "companion"
    custom_traits: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkConfig:
    """Work and productivity configuration."""
    daily_limit_hours: float = 8.0
    warning_threshold: float = 0.8
    hard_stop_enabled: bool = True
    auto_commit_message: str = "Love-Auto-Save: End of workday"
    dev_folders: list = field(default_factory=list)


@dataclass
class FinanceConfig:
    """Finance and trading configuration."""
    watchlist: list = field(default_factory=lambda: ["BTCUSDT", "ETHUSDT"])
    risk_profile: str = "moderate"
    max_position_size: float = 50000
    default_currency: str = "USD"
    exchange_api_key: str = ""
    exchange_api_secret: str = ""


@dataclass
class DevelopmentConfig:
    """Development environment configuration."""
    work_project: str = ""
    dotnet_project: str = ""
    flutter_project: str = ""
    docs_url: str = "https://docs.google.com"
    auto_tests: bool = True
    suggest_architecture: bool = True


@dataclass
class PowerProfile:
    """Hardware power profile."""
    llm_temperature: float = 0.4
    llm_max_tokens: int = 2048
    market_scan_interval: int = 5
    use_quantized: bool = False
    background_tasks: bool = True
    gpu_acceleration: bool = True


@dataclass
class DevicesConfig:
    """Device and hardware configuration."""
    primary_device_id: str = ""
    primary_device_type: str = ""
    power_profiles: Dict[str, PowerProfile] = field(default_factory=dict)


@dataclass
class ModelsConfig:
    """AI model configuration."""
    reasoning: str = "deepseek-r1:7b"
    coding: str = "qwen2.5-coder:7b"
    embedding: str = "nomic-embed-text"
    base_url: str = "http://localhost:11434"


@dataclass
class MemoryConfig:
    """Memory and sync configuration."""
    sync_enabled: bool = True
    sync_db_path: str = "./data/love_os.db"
    memory_path: str = "./data/memory"


@dataclass
class VoiceConfig:
    """Voice interface configuration."""
    wake_word: str = "Hey Love"
    stt_enabled: bool = True
    tts_enabled: bool = True
    tts_engine: str = "auto"


@dataclass
class EvolutionConfig:
    """Self-evolution configuration."""
    auto_heal_enabled: bool = True
    weekly_optimization: bool = True
    auto_install_deps: bool = True


@dataclass
class PrivacyConfig:
    """Privacy settings."""
    local_only: bool = True
    cloud_sync: bool = False
    anonymize_logs: bool = False


@dataclass
class LoveSettings:
    """Complete LOVE settings."""
    user: UserConfig = field(default_factory=UserConfig)
    companion: CompanionConfig = field(default_factory=CompanionConfig)
    work: WorkConfig = field(default_factory=WorkConfig)
    finance: FinanceConfig = field(default_factory=FinanceConfig)
    development: DevelopmentConfig = field(default_factory=DevelopmentConfig)
    devices: DevicesConfig = field(default_factory=DevicesConfig)
    models: ModelsConfig = field(default_factory=ModelsConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    
    @property
    def data_dir(self) -> Path:
        d = PROJECT_ROOT / "data"
        d.mkdir(parents=True, exist_ok=True)
        return d


class SettingsManager:
    """Manages LOVE settings loading and access."""
    
    _instance = None
    _settings: LoveSettings = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._load_settings()
        return cls._instance
    
    def _load_settings(self):
        """Load settings from YAML file."""
        # Prefer user settings, fallback to default config
        config_path = USER_CONFIG_PATH if USER_CONFIG_PATH.exists() else DEFAULT_CONFIG_PATH
        
        if not config_path.exists():
            self._settings = LoveSettings()
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            self._settings = self._parse_settings(data)
            
        except Exception as e:
            print(f"[Settings] Error loading config: {e}. Using defaults.")
            self._settings = LoveSettings()
    
    def _parse_settings(self, data: Dict[str, Any]) -> LoveSettings:
        """Parse YAML data into LoveSettings."""
        settings = LoveSettings()
        
        # Parse user config
        if 'user' in data:
            settings.user = UserConfig(**data['user'])
        
        # Parse companion config
        if 'companion' in data:
            settings.companion = CompanionConfig(**data['companion'])
        
        # Parse work config
        if 'work' in data:
            work_data = data['work'].copy()
            settings.work = WorkConfig(**work_data)
        
        # Parse finance config
        if 'finance' in data:
            settings.finance = FinanceConfig(**data['finance'])
        
        # Parse development config
        if 'development' in data:
            settings.development = DevelopmentConfig(**data['development'])
        
        # Parse devices config
        if 'devices' in data:
            devices_data = data['devices']
            power_profiles = {}
            if 'power_profiles' in devices_data:
                for key, profile in devices_data['power_profiles'].items():
                    power_profiles[key] = PowerProfile(**profile)
            settings.devices = DevicesConfig(
                primary_device_id=devices_data.get('primary_device_id', ''),
                primary_device_type=devices_data.get('primary_device_type', ''),
                power_profiles=power_profiles
            )
        
        # Parse models config
        if 'models' in data:
            settings.models = ModelsConfig(**data['models'])
        
        # Parse memory config
        if 'memory' in data:
            settings.memory = MemoryConfig(**data['memory'])
        
        # Parse voice config
        if 'voice' in data:
            settings.voice = VoiceConfig(**data['voice'])
        
        # Parse evolution config
        if 'evolution' in data:
            settings.evolution = EvolutionConfig(**data['evolution'])
        
        # Parse privacy config
        if 'privacy' in data:
            settings.privacy = PrivacyConfig(**data['privacy'])
        
        return settings
    
    def get_settings(self) -> LoveSettings:
        """Get current settings."""
        return self._settings
    
    def save_settings(self, settings: LoveSettings = None):
        """Save settings to user config file."""
        if settings:
            self._settings = settings
        
        data = self._settings_to_dict(self._settings)
        
        with open(USER_CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    def _settings_to_dict(self, settings: LoveSettings) -> Dict[str, Any]:
        """Convert LoveSettings to dictionary."""
        result = {}
        
        for key, value in asdict(settings).items():
            if isinstance(value, dict):
                result[key] = value
            else:
                result[key] = value
        
        return result
    
    def reload(self):
        """Reload settings from file."""
        self._load_settings()
    
    # Convenience properties
    @property
    def user_name(self) -> str:
        return self._settings.user.name
    
    @property
    def companion_name(self) -> str:
        return self._settings.companion.name
    
    @property
    def work_limit_hours(self) -> float:
        return self._settings.work.daily_limit_hours
    
    @property
    def watchlist(self) -> list:
        return self._settings.finance.watchlist
    
    @property
    def reasoning_model(self) -> str:
        return self._settings.models.reasoning
    
    @property
    def coding_model(self) -> str:
        return self._settings.models.coding


# Global accessor
settings = SettingsManager()

def get_settings() -> LoveSettings:
    """Get LOVE settings instance."""
    return SettingsManager().get_settings()
