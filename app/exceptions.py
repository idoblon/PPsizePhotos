class AppError(Exception):
    """Base class for application errors."""
    def __init__(self, message, status_code=500, error_code="internal_error"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

class ImageProcessingError(AppError):
    """Raised when image processing fails."""
    pass

class APIError(AppError):
    """Raised when external APIs fail."""
    pass

class QuotaExceededError(APIError):
    """Raised when API quota is exceeded."""
    def __init__(self, message="API Quota Exceeded", status_code=429, error_code="quota_exceeded"):
        super().__init__(message, status_code, error_code)

class FaceDetectionError(ImageProcessingError):
    """Raised when no face is detected."""
    def __init__(self, message="No face detected", status_code=410, error_code="face_detection_failed"):
        super().__init__(message, status_code, error_code)
