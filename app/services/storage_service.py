from supabase import create_client
import os
import uuid
import io
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if url and key:
    supabase = create_client(url, key)
else:
    supabase = None

bucket = os.getenv("SUPABASE_BUCKET", "meal-images")

def compress_image(file_content: bytes, max_size: int = 1024, quality: int = 80) -> bytes:
    """
    Resizes and compresses an image to reduce storage costs.
    Target: Max width/height 1024px, 80% quality JPEG.
    """
    img = Image.open(io.BytesIO(file_content))
    
    # Preserve orientation if EXIF present
    if hasattr(img, '_getexif'):
        img.info.get('exif')
        
    # Calculate aspect ratio
    width, height = img.size
    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        img = img.resize((new_width, new_height), Image.LANCZOS)
    
    # Convert to RGB (required for JPEG)
    if img.mode != 'RGB':
        img = img.convert('RGB')
        
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=quality, optimize=True)
    return output.getvalue()

def upload_image(file):
    """
    Compresses and uploads a file to Supabase Storage.
    Returns the public URL.
    """
    if supabase is None:
        return "https://placeholder.com/image.jpg"
        
    # Read the file content
    file_content = file.file.read()
    file.file.seek(0)

    # Apply Compression
    try:
        compressed_content = compress_image(file_content)
    except Exception as e:
        print(f"Compression failed: {str(e)}")
        compressed_content = file_content # Fallback to original if compression fails

    filename = f"{uuid.uuid4()}.jpg" # Save all as jpg after compression
    path = f"meals/{filename}"

    try:
        supabase.storage.from_(bucket).upload(
            path,
            compressed_content,
            {
                "content-type": "image/jpeg"
            }
        )

        public_url = supabase.storage.from_(bucket).get_public_url(path)
        return public_url
    except Exception as e:
        print(f"Supabase Storage Error: {str(e)}")
        return None
