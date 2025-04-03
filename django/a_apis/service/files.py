import os
import uuid
from datetime import datetime
from typing import Optional, Union

from a_apis.models.files import File
from ninja.files import UploadedFile

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction


class FileService:
    @staticmethod
    def upload_file(file: UploadedFile) -> File:
        """파일 업로드 및 File 모델 생성

        Args:
            file: 업로드할 파일 객체

        Returns:
            File: 저장된 파일 객체
        """
        try:
            # 파일명 생성 (UUID + 원본 확장자)
            original_name = file.name
            ext = original_name.split(".")[-1] if "." in original_name else ""
            filename = f"{uuid.uuid4()}.{ext.lower()}"

            # 날짜별 경로 생성
            now = datetime.now()
            date_path = now.strftime("%Y/%m/%d")
            file_path = f"uploads/{date_path}/{filename}"

            # 파일 저장
            saved_path = default_storage.save(file_path, ContentFile(file.read()))

            # 파일 크기 확인
            file_size = file.size

            # File 모델 생성
            file_obj = File.objects.create(
                file=saved_path,
                size=file_size,
                type=ext.lower(),
            )

            return file_obj

        except Exception as e:
            raise Exception(f"파일 업로드 실패: {str(e)}")

    @staticmethod
    @transaction.atomic
    def delete_file(file_obj: Union[File, int]) -> bool:
        """파일 삭제

        Args:
            file_obj: 삭제할 파일 객체 또는 ID

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # ID로 전달된 경우 객체 조회
            if isinstance(file_obj, int):
                file_obj = File.objects.get(id=file_obj)

            # 파일 시스템에서 삭제
            if default_storage.exists(file_obj.file.name):
                default_storage.delete(file_obj.file.name)

            # DB에서 삭제
            file_obj.delete()

            return True

        except File.DoesNotExist:
            print(f"파일을 찾을 수 없습니다: {file_obj}")
            return False
        except Exception as e:
            print(f"파일 삭제 실패: {str(e)}")
            return False
