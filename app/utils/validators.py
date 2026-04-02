from app.exceptions import ValidationError, InvalidFileTypeError

class RequestValidator:
    """
    Handles validation and sanitization of incoming HTTP request data.
    
    Ensures that form parameters are within acceptable bounds and that 
    uploaded files meet the required image format specifications.
    """
    
    @staticmethod
    def validate_int(value, name, min_val=None, max_val=None):
        """
        Safely parses a value into an integer and checks its range.
        
        Args:
            value (str/int): The raw value to parse.
            name (str): The parameter name (for error messages).
            min_val (int, optional): Minimum allowed value.
            max_val (int, optional): Maximum allowed value.
            
        Returns:
            int: The parsed and validated integer.
            
        Raises:
            ValidationError: If parsing fails or value is out of bounds.
        """
        try:
            val = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Parameter '{name}' must be an integer.", error_code=f"invalid_{name}")
            
        if min_val is not None and val < min_val:
            raise ValidationError(f"'{name}' cannot be less than {min_val}.", error_code=f"{name}_too_small")
            
        if max_val is not None and val > max_val:
            raise ValidationError(f"'{name}' cannot be greater than {max_val}.", error_code=f"{name}_too_large")
            
        return val

    @staticmethod
    def validate_image_file(file):
        """
        Validates that an uploaded file is a supported image type.
        
        Checks the file extension against a whitelist of expected formats.
        
        Args:
            file (werkzeug.datastructures.FileStorage): The uploaded file object.
            
        Returns:
            bool: True if the file is valid.
            
        Raises:
            InvalidFileTypeError: If the file format is not supported.
        """
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
        
        if not file or file.filename == '':
            return False
            
        filename = file.filename.lower()
        if not ('.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS):
            raise InvalidFileTypeError(f"File '{filename}' is not a supported image format.")
            
        return True

    @classmethod
    def validate_process_request(cls, form_data, files):
        """
        Aggregates validation for the full /process multi-part request.
        
        Parses dimensions, spacing, borders, and all uploaded images with 
        their respective copy counts.
        
        Returns:
            dict: Validated parameters and list of image files.
        """
        validated = {}
        
        # 1. Base layout parameters
        # Restrict dimensions to prevent excessive resource consumption
        validated['width'] = cls.validate_int(form_data.get('width', 390), 'width', min_val=100, max_val=2000)
        validated['height'] = cls.validate_int(form_data.get('height', 480), 'height', min_val=100, max_val=2000)
        validated['spacing'] = cls.validate_int(form_data.get('spacing', 10), 'spacing', min_val=0, max_val=100)
        validated['border'] = cls.validate_int(form_data.get('border', 2), 'border', min_val=0, max_val=20)
        
        # 2. Image collection (supports multi-image upload keys)
        images_data = []
        i = 0
        while f"image_{i}" in files:
            img_file = files[f"image_{i}"]
            cls.validate_image_file(img_file)
            
            # Limit copies per image to keep PDF sizes manageable
            copies = cls.validate_int(form_data.get(f"copies_{i}", 6), f"copies_{i}", min_val=1, max_val=54)
            images_data.append((img_file, copies))
            i += 1
            
        # Fallback to single image upload (legacy support)
        if not images_data and "image" in files:
            img_file = files["image"]
            cls.validate_image_file(img_file)
            copies = cls.validate_int(form_data.get("copies", 6), "copies", min_val=1, max_val=54)
            images_data.append((img_file, copies))
            
        if not images_data:
            raise ValidationError("No valid images were uploaded.", error_code="no_image_uploaded")
            
        validated['images_data'] = images_data
        return validated
