from pydantic import BaseModel, Field
from typing import Optional


class Text(BaseModel):
    path: Optional[str] = Field(
        None,
        description="name of the text file",
    )

    content: str = Field(
        None,
        description="content of the text file",
    )

    error: Optional[str] = Field(
        None,
        description="error message",
    )
