from pydantic import BaseModel

class ReceiverSessionModel(BaseModel):
    session_id: str
    status: str = "waiting"
    transfer_id: str | None = None
    # Opaque client-side ECDH-sealed ciphertext. Never a plaintext AES key.
    wrapped_key: str | None = None
    created_at: str
    expires_at: str
