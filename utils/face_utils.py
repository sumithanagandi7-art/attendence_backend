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


def extract_face_encoding(image_path):
    """
    Load an image from disk and return the 128-d encoding of the first
    detected face. Returns None if no face (or more than one face) is found.
    """
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)

    if len(face_locations) == 0:
        return None, "No face detected in the image."
    if len(face_locations) > 1:
        return None, "Multiple faces detected — please submit a photo with only one face."

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
