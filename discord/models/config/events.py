from redis_om import EmbeddedJsonModel, Field
from typing import Optional

class EventSettingsModel(EmbeddedJsonModel):
    channel: int = Field(index=False)
    role: Optional[int] = Field(index=False, default=None)