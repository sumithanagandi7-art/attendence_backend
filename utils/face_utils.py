"""
Face recognition helpers built on top of the `face_recognition` library
(which wraps dlib's HOG/CNN face detector + a ResNet face-embedding model).

Each face is reduced to a 128-dimensional numeric encoding. Two faces are
considered a match if the Euclidean distance between their encodings is
below FACE_MATCH_TOLERANCE (lower = stricter).
"""
import os
import uuid
import face_recognition
import numpy as np
from PIL import Image, ExifTags

# Maximum pixel dimension — larger images are downscaled to this before
# running face detection.  Keeps memory usage and processing time low on
# Render's free tier while still being large enough for reliable detection.
_MAX_DIMENSION = 800


def _preprocess_image(image_path):
    """
    Prepare a mobile-camera photo for reliable face detection:
      1. Auto-rotate based on EXIF orientation (front cameras often embed
         rotation metadata instead of actually rotating the pixel data).
      2. Resize so the longest side is at most _MAX_DIMENSION pixels.
    Overwrites the file in-place and returns the path.
    """
    try:
        img = Image.open(image_path)

        # --- EXIF auto-rotate ---
        try:
            # Pillow >=6.0 convenience method
            img = _apply_exif_rotation(img)
        except Exception:
            pass  # If EXIF parsing fails, proceed with the image as-is

        # --- Resize if too large ---
        w, h = img.size
        if max(w, h) > _MAX_DIMENSION:
            scale = _MAX_DIMENSION / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        img.save(image_path, quality=90)
    except Exception:
        pass  # If preprocessing fails, let face_recognition try the raw file

    return image_path


def _apply_exif_rotation(img):
    """Rotate a PIL Image according to its EXIF Orientation tag."""
    exif = img.getexif()
    if not exif:
        return img

    orientation_key = None
    for k, v in ExifTags.TAGS.items():
        if v == "Orientation":
            orientation_key = k
            break

    if orientation_key is None or orientation_key not in exif:
        return img

    orientation = exif[orientation_key]
    if orientation == 3:
        img = img.rotate(180, expand=True)
    elif orientation == 6:
        img = img.rotate(270, expand=True)
    elif orientation == 8:
        img = img.rotate(90, expand=True)

    return img


def extract_face_encoding(image_path):
    """
    Load an image from disk and return the 128-d encoding of the first
    detected face.

    Detection strategy (HOG only — CNN is too memory-heavy for free-tier):
      1. Try HOG with upsample=1 (standard, fast).
      2. If no face found, retry with upsample=2 (catches smaller/distant faces).

    Returns (encoding_list, None) on success or (None, error_string) on failure.
    """
    # Pre-process: auto-rotate and resize for reliability
    _preprocess_image(image_path)

    image = face_recognition.load_image_file(image_path)

    # --- Attempt 1: HOG model with standard upsample ---
    face_locations = face_recognition.face_locations(
        image, number_of_times_to_upsample=1, model="hog"
    )

    # --- Attempt 2: HOG model with more upsampling for smaller faces ---
    if len(face_locations) == 0:
        face_locations = face_recognition.face_locations(
            image, number_of_times_to_upsample=2, model="hog"
        )

    if len(face_locations) == 0:
        return None, "No face detected in the image. Please use good lighting, face the camera directly, and remove masks or sunglasses."
    if len(face_locations) > 1:
        # Use only the largest face instead of rejecting
        face_locations = [max(face_locations, key=lambda r: (r[2] - r[0]) * (r[1] - r[3]))]

    encodings = face_recognition.face_encodings(image, known_face_locations=face_locations)
    return encodings[0].tolist(), None


def compare_faces(known_encoding, candidate_encoding, tolerance=0.5):
    """
    Compare a stored encoding (list of 128 floats) against a freshly
    captured encoding. Returns (is_match: bool, distance: float).
    """
    known = np.array(known_encoding)
    candidate = np.array(candidate_encoding)
    distance = float(np.linalg.norm(known - candidate))
    return distance <= tolerance, distance


def save_uploaded_image(file_storage, upload_dir):
    """Save an uploaded image (Flask FileStorage) to disk with a unique name."""
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(file_storage.filename)[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(upload_dir, filename)
    file_storage.save(path)
    return path

