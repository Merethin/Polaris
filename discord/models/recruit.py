from redis_om import JsonModel, Field

class APITemplateModel(JsonModel):
    id: str = Field(index=True)
    tgid: str = Field(index=False)
    secretKey: str = Field(index=False)

    class Meta:
        global_key_prefix = "APITemplate"
        index_name = "api_template_idx"

class UserTemplateModel(JsonModel):
    id: str = Field(index=True)
    user: int = Field(index=True)
    tgid: str = Field(index=False)

    class Meta:
        global_key_prefix = "UserTemplate"
        index_name = "user_template_idx"

class TemplateModel(JsonModel):
    id: str = Field(index=True)
    bucket: str = Field(index=True)
    mode: int = Field(index=True)
    content: str = Field(index=False)

    class Meta:
        global_key_prefix = "Template"
        index_name = "template_idx"

class BucketModel(JsonModel):
    id: str = Field(index=True)
    filter: str = Field(index=False)
    size: int = Field(index=False)
    priority: float = Field(index=False)
    mode: int = Field(index=True)
    templates: list[str] = Field(index=False)

    class Meta:
        global_key_prefix = "Bucket"
        index_name = "bucket_idx"