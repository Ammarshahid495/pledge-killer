"""
Submission and Version Management Service.
Validates file safety (rejects binaries, archives, executables) and handles versioning.
"""

from datetime import datetime, timezone
import os
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from ..core.config import settings
from ..models.classroom import Classroom, ClassroomMember
from ..models.submission import Submission, SubmissionVersion
from ..models.user import User
from ..storage.storage_driver import StorageDriver
from ..storage.local_storage import get_storage_driver


# Binary signatures to reject
BINARY_MAGIC_PREFIXES = [
    b"\x7fELF",  # Linux ELF executable
    b"MZ",       # Windows DOS/PE executable
    b"\xca\xfe\xba\xbe",  # Java class / Mach-O universal
    b"\xfe\xed\xfa\xce",  # Mach-O 32-bit
    b"\xfe\xed\xfa\xcf",  # Mach-O 64-bit
    b"\xce\xfa\xed\xfe",  # Mach-O reverse
    b"\xcf\xfa\xed\xfe",  # Mach-O reverse
    b"PK\x03\x04",        # ZIP archive
    b"\x1f\x8b",          # GZIP
    b"BZh",               # BZIP2
    b"7z\xbc\xaf\x27\x1c", # 7z archive
    b"Rar!\x1a\x07",      # RAR archive
    b"\x00\x00\x00",      # Common binary header
]


class SubmissionValidationError(Exception):
    pass


class SubmissionService:
    @staticmethod
    def validate_cpp_file(filename: str, content: bytes) -> str:
        """
        Validates the uploaded file.
        Returns decoded source code string.
        Raises SubmissionValidationError on invalid input.
        """
        if not filename or not filename.lower().endswith(".cpp"):
            raise SubmissionValidationError("Only .cpp files are accepted")

        file_size = len(content)
        if file_size == 0:
            raise SubmissionValidationError("File is empty")

        if file_size > 1_048_576:  # 1 MB
            raise SubmissionValidationError("File size exceeds 1 MB limit")

        # Check binary magic prefixes
        for magic in BINARY_MAGIC_PREFIXES:
            if content.startswith(magic):
                raise SubmissionValidationError("Executable or archive files are strictly prohibited")

        # Check for null bytes (typical indicator of binary data)
        if b"\x00" in content:
            raise SubmissionValidationError("Binary content detected; only text C++ source files are allowed")

        # Attempt UTF-8 or ASCII decoding
        try:
            decoded = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                decoded = content.decode("latin-1")
            except Exception:
                raise SubmissionValidationError("File encoding could not be decoded as text")

        # Strip whitespace and verify there is actual content
        if not decoded.strip():
            raise SubmissionValidationError("Source file contains only whitespace")

        return decoded

    @staticmethod
    def submit_assignment(
        db: Session,
        classroom_id: str,
        user: User,
        filename: str,
        content: bytes,
        storage: Optional[StorageDriver] = None,
    ) -> Tuple[Submission, SubmissionVersion, bool]:
        """
        Processes a submission or replacement version.
        Returns (submission, version, threshold_just_reached).
        """
        storage = storage or get_storage_driver()

        # 1. Verify classroom
        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom or classroom.status in ("EXPIRED", "CANCELLED"):
            raise ValueError("Classroom is not active or has expired")

        if classroom.deadline:
            dl = classroom.deadline
            if dl.tzinfo is None:
                dl = dl.replace(tzinfo=timezone.utc)
            if dl < datetime.now(timezone.utc):
                raise ValueError("Classroom deadline has passed; submissions are closed")

        # 2. Verify membership
        member = (
            db.query(ClassroomMember)
            .filter(
                ClassroomMember.classroom_id == classroom_id,
                ClassroomMember.user_id == user.id,
                ClassroomMember.status == "ACTIVE",
            )
            .first()
        )
        if not member:
            raise ValueError("You are not an active member of this classroom")

        # 3. Validate content
        source_code = SubmissionService.validate_cpp_file(filename, content)

        # 4. Save to storage
        storage_key, sha256_hash, file_size = storage.save_file(content, extension=".cpp")

        # 5. Check if submission record already exists for this member
        submission = (
            db.query(Submission)
            .filter(
                Submission.classroom_id == classroom_id,
                Submission.member_id == member.id,
            )
            .first()
        )

        is_new_participant_submission = False
        if not submission:
            submission = Submission(
                classroom_id=classroom_id,
                member_id=member.id,
                status="ACTIVE",
            )
            db.add(submission)
            db.flush()
            version_num = 1
            is_new_participant_submission = True
        else:
            submission.status = "ACTIVE"
            submission.updated_at = datetime.now(timezone.utc)
            # Count existing versions
            latest_version = (
                db.query(SubmissionVersion)
                .filter(SubmissionVersion.submission_id == submission.id)
                .order_by(SubmissionVersion.version_number.desc())
                .first()
            )
            version_num = (latest_version.version_number + 1) if latest_version else 1

        # Create new version record
        version = SubmissionVersion(
            submission_id=submission.id,
            version_number=version_num,
            storage_key=storage_key,
            sha256_hash=sha256_hash,
            file_size=file_size,
            original_filename=os.path.basename(filename),
            language="cpp",
            processing_status="PROCESSED",
        )
        db.add(version)
        db.flush()

        submission.current_version_id = version.id
        db.commit()
        db.refresh(submission)
        db.refresh(version)

        # 6. Check submission threshold
        active_submissions_count = (
            db.query(Submission)
            .filter(
                Submission.classroom_id == classroom_id,
                Submission.status == "ACTIVE",
                Submission.current_version_id.isnot(None),
            )
            .count()
        )

        min_required = classroom.min_submissions if classroom.min_submissions else settings.MIN_SUBMISSION_THRESHOLD
        should_trigger_analysis = active_submissions_count >= min_required

        return submission, version, should_trigger_analysis

    @staticmethod
    def get_user_active_submission(
        db: Session,
        classroom_id: str,
        user_id: str,
        storage: Optional[StorageDriver] = None,
    ) -> Tuple[Optional[Submission], Optional[SubmissionVersion], Optional[str]]:
        """
        Retrieves user's own active submission and source code.
        NEVER expose another student's source code!
        """
        storage = storage or get_storage_driver()

        member = (
            db.query(ClassroomMember)
            .filter(
                ClassroomMember.classroom_id == classroom_id,
                ClassroomMember.user_id == user_id,
                ClassroomMember.status == "ACTIVE",
            )
            .first()
        )
        if not member:
            return None, None, None

        submission = (
            db.query(Submission)
            .filter(
                Submission.classroom_id == classroom_id,
                Submission.member_id == member.id,
                Submission.status == "ACTIVE",
            )
            .first()
        )
        if not submission or not submission.current_version_id:
            return None, None, None

        version = (
            db.query(SubmissionVersion)
            .filter(SubmissionVersion.id == submission.current_version_id)
            .first()
        )

        raw_code = None
        if version:
            content_bytes = storage.get_file_content(version.storage_key)
            if content_bytes:
                raw_code = content_bytes.decode("utf-8", errors="replace")

        return submission, version, raw_code

    @staticmethod
    def remove_user_submission(db: Session, classroom_id: str, user_id: str) -> bool:
        """
        Removes / withdraws the user's active submission file from the classroom.
        Ensures strict participant isolation: user can only withdraw their own file.
        """
        member = (
            db.query(ClassroomMember)
            .filter(
                ClassroomMember.classroom_id == classroom_id,
                ClassroomMember.user_id == user_id,
                ClassroomMember.status == "ACTIVE",
            )
            .first()
        )
        if not member:
            raise ValueError("You are not an active member of this classroom")

        submission = (
            db.query(Submission)
            .filter(
                Submission.classroom_id == classroom_id,
                Submission.member_id == member.id,
            )
            .first()
        )
        if not submission or submission.status == "WITHDRAWN":
            return False

        submission.status = "WITHDRAWN"
        submission.current_version_id = None
        db.commit()
        return True
