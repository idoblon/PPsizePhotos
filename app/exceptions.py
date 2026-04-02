class AppError(Exception):
    """
    Base class for all application-specific errors.
    
    Provides a standardized way to return error messages and HTTP status 
    codes to the frontend.
    """
    def __init__(self, message, status_code=500, error_code="internal_error"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

class ValidationError(AppError):
    """
    Raised when the incoming request parameters (width, copies, etc.) 
    fail validation checks.
    """
    def __init__(self, message="Invalid parameters", status_code=422, error_code="validation_failed"):
        super().__init__(message, status_code, error_code)

class ImageProcessingError(AppError):
    """Base class for errors occurring during the image transformation pipeline."""
    pass

class APIError(AppError):
    """Raised when an external service (Remove.bg, Cloudinary) returns an error."""
    pass

class QuotaExceededError(APIError):
    """Raised when an external API's usage limit has been reached."""
    def __init__(self, message="API Quota Exceeded", status_code=429, error_code="quota_exceeded"):
        super().__init__(message, status_code, error_code)

class FaceDetectionError(ImageProcessingError):
    """Raised when the AI service is unable to locate a face in the provided image."""
    def __init__(self, message="No face detected", status_code=410, error_code="face_detection_failed"):
        super().__init__(message, status_code, error_code)

class InvalidFileTypeError(ValidationError):
    """Raised when an uploaded file is not a supported image format."""
    def __init__(self, message="Invalid file type", status_code=400, error_code="invalid_file_type"):
        super().__init__(message, status_code, error_code)
