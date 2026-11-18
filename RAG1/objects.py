from pydantic import BaseModel, Field


class Answer(BaseModel):
    answer: str = Field(description="The answer that is needed for the user question")
    context: str = Field(
        default="",
        description="The context from the healthcare leaflets used to generate the answer",
    )


