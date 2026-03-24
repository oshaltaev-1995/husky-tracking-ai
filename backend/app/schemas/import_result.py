from pydantic import BaseModel


class ImportResult(BaseModel):
    dogs_created: int
    dogs_updated: int
    worklogs_created: int
    worklogs_updated: int