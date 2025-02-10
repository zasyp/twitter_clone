from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


class DefaultSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    result: bool = True


class TweetIn(BaseModel):
	tweet_data: str
	tweet_media_ids: Optional[List[int]]


class MediaUpload(DefaultSchema):
    id: int = Field(alias="media_id")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
