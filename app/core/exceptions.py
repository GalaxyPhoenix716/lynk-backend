class LynkException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
        
class TransferNotFoundException(LynkException):
    def __init__(self, message: str = "Transfer not found or expired"):
        super().__init__(message, status_code=404)

class TransferNotReadyException(LynkException):
    def __init__(self, message: str = "Transfer is not ready"):
        super().__init__(message, status_code=409)
        
class LimitExceededException(LynkException):
    def __init__(self, message: str):
        super().__init__(message, status_code=413)
        
class RateLimitExceededException(LynkException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)
class ServiceUnavailableException(LynkException):
    def __init__(self, message: str = "Redis or R2 storage unavailable"):
        super().__init__(message, status_code=503)