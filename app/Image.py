from pydantic import BaseModel, Field
from typing import Optional


class Image(BaseModel):
    base64: Optional[str] = Field(
        None,
        description="base64 encoded image (data:image/png;base64,iVBOR...)",
    )

    description: Optional[str] = Field(
        None,
        description="description of the image",
    )

    error: Optional[str] = Field(
        None,
        description="error message",
    )
