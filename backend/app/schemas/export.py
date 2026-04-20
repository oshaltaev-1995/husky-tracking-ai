from pydantic import BaseModel


class RawRunLogExportInfo(BaseModel):
    rows: int
    filename: str