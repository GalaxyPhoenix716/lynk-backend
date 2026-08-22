from pydantic import BaseModel

class ReceiverSessionCreateResponse(BaseModel):
    session_id: str
    status: str
    expires_in: int

class ReceiverSessionResponse(BaseModel):
    session_id: str
    status: str
    transfer_id: str | None = None
    wrapped_key: str | None = None
    expires_in: int

class AttachTransferRequest(BaseModel):
    transfer_id: str
    # Opaque ECDH-sealed ciphertext of the AES key, wrapped client-side to the
    # receiver's ephemeral public key. The backend never sees the plaintext.
    wrapped_key: str | None = None
