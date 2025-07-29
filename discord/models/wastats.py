from redis_om import JsonModel, Field

class WaStats(JsonModel):
    timestamp: float = Field(index=True)
    waCount: int = Field(index=False)
    delEndos: int = Field(index=False)
    endosGiven: int = Field(index=False)
    potentialEndos: int = Field(index=False)

    def delegateRatio(self) -> float:
        return self.delEndos / (self.waCount - 1)
    
    def regionRatio(self) -> float:
        return self.endosGiven / self.potentialEndos
    
    class Meta:
        global_key_prefix = "WaStats"
        index_name = "wa_stats_idx"