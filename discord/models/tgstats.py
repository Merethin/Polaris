from redis_om import JsonModel, Field

class TelegramStats(JsonModel):
    timestamp: float = Field(index=True)
    sender: int = Field(index=True)
    senderDisplayName: str = Field(index=False)
    bucket: str = Field(index=False)
    template: str = Field(index=False)
    recipientCount: int = Field(index=False)
    
    class Meta:
        global_key_prefix = "TelegramStats"
        index_name = "telegram_stats_idx"