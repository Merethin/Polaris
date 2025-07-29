from redis_om import JsonModel, Field
from typing import Optional

class EventSettingsModel(JsonModel):
    event: str = Field(index=True)
    channel: int = Field(index=False)
    role: Optional[int] = Field(index=False)

    class Meta:
        global_key_prefix = "EventSettings"
        index_name = "event_settings_idx"