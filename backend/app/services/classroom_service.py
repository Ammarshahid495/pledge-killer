"""
Classroom Management Service adhering to the Equal Permissions Principle.
"""

from datetime import datetime, timezone
import string
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from ..core.security import generate_secure_token, hash_token
from ..models.analysis import SimilarityMatch
from ..models.classroom import Classroom, ClassroomMember
from ..models.submission import Submission
from ..models.user import User
from ..schemas.classroom import ClassroomCreate
from ..storage.local_storage import get_storage_driver
from ..storage.storage_driver import StorageDriver


def int_to_label(index: int) -> str:
    """Converts a 0-based index to Peer A, Peer B, ..., Peer Z, Peer AA, etc."""
    label = ""
    index += 1
    while index > 0:
        index, rem = divmod(index - 1, 26)
        label = chr(65 + rem) + label
    return f"Peer {label}"


class ClassroomService:
    @staticmethod
    def create_classroom(db: Session, creator: User, req: ClassroomCreate, base_url: str = "") -> Tuple[Classroom, str]:
        raw_token = generate_secure_token(32)
        token_hash = hash_token(raw_token)

        classroom = Classroom(
            title=req.title.strip(),
            description=req.description.strip() if req.description else None,
            join_token=raw_token,
            join_token_hash=token_hash,
            language="cpp",
            status="ACTIVE",
            min_submissions=req.min_submissions or 5,
            deadline=req.deadline,
            max_participants=req.max_participants,
        )
        db.add(classroom)
        db.flush()

        # Creator is simply the first participant with anonymous label 'Peer A'
        creator_membership = ClassroomMember(
            classroom_id=classroom.id,
            user_id=creator.id,
            anonymous_label=int_to_label(0),
            status="ACTIVE",
        )
        db.add(creator_membership)
        db.commit()
        db.refresh(classroom)

        join_url = f"/join/{raw_token}"
        return classroom, join_url

    @staticmethod
    def join_classroom(db: Session, user: User, raw_join_token: str) -> Classroom:
        clean_token = raw_join_token.strip()
        if "/join/" in clean_token:
            clean_token = clean_token.split("/join/")[-1]
        elif "/classrooms/" in clean_token:
            clean_token = clean_token.split("/classrooms/")[-1]
        clean_token = clean_token.split("?")[0].split("#")[0].strip("/").strip()

        token_hash = hash_token(clean_token)
        classroom = (
            db.query(Classroom)
            .filter(
                (Classroom.join_token == clean_token)
                | (Classroom.join_token_hash == token_hash)
                | (Classroom.join_token_hash == clean_token)
                | (Classroom.id == clean_token)
            )
            .first()
        )

        if not classroom:
            raise ValueError("Invalid classroom joining link or token")

        # Ensure join_token is populated
        if not classroom.join_token:
            classroom.join_token = generate_secure_token(32)
            classroom.join_token_hash = hash_token(classroom.join_token)
            db.commit()
            db.refresh(classroom)

        if classroom.status in ("EXPIRED", "CANCELLED"):
            raise ValueError("This classroom is no longer active")

        # Check deadline
        if classroom.deadline:
            dl = classroom.deadline
            if dl.tzinfo is None:
                dl = dl.replace(tzinfo=timezone.utc)
            if dl < datetime.now(timezone.utc):
                classroom.status = "EXPIRED"
                db.commit()
                raise ValueError("This classroom has expired past its deadline")

        # Check existing membership
        existing = (
            db.query(ClassroomMember)
            .filter(ClassroomMember.classroom_id == classroom.id, ClassroomMember.user_id == user.id)
            .first()
        )
        if existing:
            if existing.status == "ACTIVE":
                return classroom
            else:
                existing.status = "ACTIVE"
                db.commit()
                return classroom

        # Check participant limit
        current_members = (
            db.query(ClassroomMember)
            .filter(ClassroomMember.classroom_id == classroom.id, ClassroomMember.status == "ACTIVE")
            .count()
        )
        if classroom.max_participants and current_members >= classroom.max_participants:
            raise ValueError("Classroom has reached maximum participant capacity")

        # Assign next anonymous label
        next_label = int_to_label(current_members)
        membership = ClassroomMember(
            classroom_id=classroom.id,
            user_id=user.id,
            anonymous_label=next_label,
            status="ACTIVE",
        )
        db.add(membership)
        db.commit()
        db.refresh(classroom)
        return classroom

    @staticmethod
    def get_classroom_counts(db: Session, classroom_id: str) -> Tuple[int, int]:
        """
        Returns (participant_count, valid_submission_count).
        Valid submission count is the count of distinct participants with an active valid submission.
        """
        participant_count = (
            db.query(ClassroomMember)
            .filter(ClassroomMember.classroom_id == classroom_id, ClassroomMember.status == "ACTIVE")
            .count()
        )

        valid_submission_count = (
            db.query(Submission)
            .filter(
                Submission.classroom_id == classroom_id,
                Submission.status == "ACTIVE",
                Submission.current_version_id.isnot(None),
            )
            .count()
        )
        return participant_count, valid_submission_count

    @staticmethod
    def get_user_classrooms(db: Session, user_id: str) -> List[Classroom]:
        return (
            db.query(Classroom)
            .join(ClassroomMember, ClassroomMember.classroom_id == Classroom.id)
            .filter(ClassroomMember.user_id == user_id, ClassroomMember.status == "ACTIVE")
            .order_by(Classroom.created_at.desc())
            .all()
        )

    @staticmethod
    def _invalidate_matches(db: Session, classroom_id: str) -> None:
        matches = db.query(SimilarityMatch).filter(SimilarityMatch.classroom_id == classroom_id).all()
        for match in matches:
            db.delete(match)

    @staticmethod
    def set_starter_template(
        db: Session,
        classroom_id: str,
        filename: str,
        content: bytes,
        storage: Optional[StorageDriver] = None,
    ) -> Classroom:
        from .submission_service import SubmissionService

        storage = storage or get_storage_driver()
        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom:
            raise ValueError("Classroom not found")

        SubmissionService.validate_cpp_file(filename, content)
        if classroom.starter_storage_key:
            storage.delete_file(classroom.starter_storage_key)

        storage_key, sha256_hash, _size = storage.save_file(content, extension=".cpp")
        classroom.starter_storage_key = storage_key
        classroom.starter_filename = filename
        classroom.starter_sha256 = sha256_hash
        ClassroomService._invalidate_matches(db, classroom_id)
        db.commit()
        db.refresh(classroom)
        return classroom

    @staticmethod
    def clear_starter_template(
        db: Session,
        classroom_id: str,
        storage: Optional[StorageDriver] = None,
    ) -> Classroom:
        storage = storage or get_storage_driver()
        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom:
            raise ValueError("Classroom not found")

        if classroom.starter_storage_key:
            storage.delete_file(classroom.starter_storage_key)
        classroom.starter_storage_key = None
        classroom.starter_filename = None
        classroom.starter_sha256 = None
        ClassroomService._invalidate_matches(db, classroom_id)
        db.commit()
        db.refresh(classroom)
        return classroom

    @staticmethod
    def get_starter_source(classroom: Classroom, storage: Optional[StorageDriver] = None) -> Optional[str]:
        if not classroom.starter_storage_key:
            return None
        storage = storage or get_storage_driver()
        raw = storage.get_file_content(classroom.starter_storage_key)
        if not raw:
            return None
        return raw.decode("utf-8", errors="replace")
