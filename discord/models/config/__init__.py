from redis_om import JsonModel, Field
from typing import Optional, Self
from .events import EventSettingsModel

class ConfigModel(JsonModel):
    recruitRole: Optional[int] = Field(index=False, default=None)
    events: dict[str, EventSettingsModel] = Field(index=False, default={})

    class Meta:
        global_key_prefix = "Config"
        index_name = "config_idx"

    @classmethod
    def load(cls) -> Self:
        all_pks = cls.all_pks()

        settings = [cls.get(pk) for pk in all_pks]

        if len(settings) == 0:
            return cls()
        
        # We only need one
        for config in settings[1:]:
            cls.delete(config.pk)
        
        return settings[0]