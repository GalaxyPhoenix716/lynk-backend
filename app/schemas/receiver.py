from pydantic import BaseModel

class ReceiverSessionCreateResponse(BaseModel):
    session_id: str
    status: str
    expires_in: int

class ReceiverSessionResponse(BaseModel):
    session_id: str
    status: str
    transfer_id: str | None = None
    expires_in: int

class AttachTransferRequest(BaseModel):
    transfer_id: str
