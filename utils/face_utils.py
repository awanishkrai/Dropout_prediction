"""
Face detection and recognition utilities using OpenCV.
"""
import cv2
import numpy as np
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
import base64
from utils.db import get_db_session
from utils.models import Student


def detect_faces(image: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    Detect faces in an image using OpenCV's Haar Cascade.
    
    Args:
        image: BGR image array from OpenCV
    
    Returns:
        List of (x, y, w, h) tuples for each detected face
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Load Haar Cascade classifier
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    
    return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]


def extract_face_embedding(image: np.ndarray, face_rect: Tuple[int, int, int, int]) -> np.ndarray:
    """
    Extract a simple histogram-based embedding for a face.
    
    This is a simplified approach using color histograms.
    For production, consider using deep learning models like FaceNet.
    
    Args:
        image: BGR image array
        face_rect: (x, y, w, h) tuple
    
    Returns:
        Normalized feature vector
    """
    x, y, w, h = face_rect
    face_img = image[y:y+h, x:x+w]
    
    # Resize to standard size
    face_img = cv2.resize(face_img, (100, 100))
    
    # Convert to HSV for better color representation
    hsv = cv2.cvtColor(face_img, cv2.COLOR_BGR2HSV)
    
    # Calculate histograms for each channel
    hist_h = cv2.calcHist([hsv], [0], None, [50], [0, 180])
    hist_s = cv2.calcHist([hsv], [1], None, [60], [0, 256])
    hist_v = cv2.calcHist([hsv], [2], None, [60], [0, 256])
    
    # Concatenate and normalize
    embedding = np.concatenate([
        hist_h.flatten(),
        hist_s.flatten(),
        hist_v.flatten()
    ])
    embedding = embedding / (np.linalg.norm(embedding) + 1e-6)
    
    return embedding


def compare_embeddings(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """
    Compare two embeddings using cosine similarity.
    
    Returns:
        Similarity score between 0 and 1
    """
    return float(np.dot(emb1, emb2))


def find_matching_student(
    face_embedding: np.ndarray,
    threshold: float = 0.7
) -> Optional[Dict[str, Any]]:
    """
    Find a matching student for the given face embedding.
    
    Args:
        face_embedding: Face embedding to match
        threshold: Minimum similarity threshold
    
    Returns:
        Student dict (id, name) if match found, None otherwise
    """
    session = get_db_session()
    best_match = None
    best_score = threshold
    
    try:
        students = session.query(Student).all()
        
        for student in students:
            stored_emb_list = student.get_embedding()
            if stored_emb_list is None:
                continue
                
            stored_embedding = np.array(stored_emb_list)
            score = compare_embeddings(face_embedding, stored_embedding)
            
            if score > best_score:
                best_score = score
                best_match = {
                    "student_id": student.student_id,
                    "name": student.name
                }
    except Exception as e:
        print(f"Error matching student: {e}")
    finally:
        session.close()
    
    return best_match


def store_face_embedding(student_id: str, embedding: np.ndarray) -> bool:
    """
    Store a face embedding for a student.
    
    Args:
        student_id: Student ID
        embedding: Face embedding array
    
    Returns:
        True if successful
    """
    session = get_db_session()
    try:
        student = session.query(Student).filter_by(student_id=student_id).first()
        if student:
            student.set_embedding(embedding.tolist())
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


def draw_face_boxes(
    image: np.ndarray,
    faces: List[Tuple[int, int, int, int]],
    labels: Optional[List[str]] = None
) -> np.ndarray:
    """
    Draw bounding boxes around detected faces.
    
    Args:
        image: BGR image array
        faces: List of (x, y, w, h) tuples
        labels: Optional list of labels for each face
    
    Returns:
        Image with drawn boxes
    """
    output = image.copy()
    
    for i, (x, y, w, h) in enumerate(faces):
        # Draw rectangle
        cv2.rectangle(output, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Draw label if provided
        if labels and i < len(labels):
            label = labels[i]
            cv2.putText(
                output, label, (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 255, 0), 2
            )
    
    return output


def image_to_base64(image: np.ndarray) -> str:
    """Convert OpenCV image to base64 string."""
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')


def base64_to_image(base64_str: str) -> np.ndarray:
    """Convert base64 string to OpenCV image."""
    img_data = base64.b64decode(base64_str)
    nparr = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
