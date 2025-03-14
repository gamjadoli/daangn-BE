import uuid

from a_apis.models import File

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


class FileService:
    @staticmethod
    def upload_file(uploaded_file) -> File:
        """파일 업로드 및 File 모델 생성"""
        try:
            # 파일명 생성 (UUID + 원본 확장자)
            original_name = uploaded_file.name
            ext = original_name.split(".")[-1] if "." in original_name else ""
            filename = f"{uuid.uuid4()}.{ext}"

            # S3에 파일 업로드
            path = default_storage.save(
                f"products/{filename}", ContentFile(uploaded_file.read())
            )

            # File 모델 생성
            file_instance = File.objects.create(
                original_name=original_name,
                file=path,
                content_type=uploaded_file.content_type,
                size=uploaded_file.size,
            )

            return file_instance

        except Exception as e:
            raise Exception(f"파일 업로드 실패: {str(e)}")
