from pydantic import BaseModel, Field

class GoogleEmailDetails(BaseModel):
    subject: str = Field(description="The subject of the email.")
    sender: str = Field(description="The email address of the sender.")
    receiver: str = Field(description="The email address of the receiver.")
    text: str = Field(description="The text content of the email.")

    class Config:
        arbitrary_types_allowed = True

