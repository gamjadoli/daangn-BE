import os
import time
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
    # 지원하는 파일 타입 정의
    IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"]
    VIDEO_EXTENSIONS = ["mp4", "avi", "mov", "wmv", "flv", "mkv", "webm"]

    @staticmethod
    def get_file_type(extension: str) -> str:
        """파일 확장자로 파일 유형(이미지/비디오) 결정

        Args:
            extension: 파일 확장자

        Returns:
            str: 'image' 또는 'video' 또는 'file'
        """
        ext = extension.lower()
        if ext in FileService.IMAGE_EXTENSIONS:
            return "image"
        elif ext in FileService.VIDEO_EXTENSIONS:
            return "video"
        else:
            return "file"

    @staticmethod
    def upload_file(file: UploadedFile, file_type: str = None) -> File:
        """파일 업로드 및 File 모델 생성

        Args:
            file: 업로드할 파일 객체
            file_type: 파일 용도 (product, profile 등). None이면 자동 추론

        Returns:
            File: 저장된 파일 객체
        """
        try:
            # 확장자 추출
            original_name = file.name
            ext = original_name.split(".")[-1] if "." in original_name else ""

            # 파일 미디어 타입 결정 (이미지/비디오/기타)
            media_type = FileService.get_file_type(ext)

            # 타임스탬프 생성
            timestamp = int(time.time())

            # 짧은 UUID 생성 (처음 8자리만 사용)
            short_uuid = str(uuid.uuid4()).split("-")[0]

            # 용도가 명시되지 않은 경우 미디어 타입을 용도로 사용
            purpose = file_type or "product"

            # 파일명 형식: 용도-타임스탬프-UUID.확장자
            filename = f"{purpose}-{timestamp}-{short_uuid}.{ext.lower()}"

            # 간결한 날짜별 경로 생성 (년/월 형식)
            now = datetime.now()
            date_path = now.strftime("%Y/%m")

            # 미디어 타입에 따른 경로 결정
            file_path = (
                f"{media_type}s/{date_path}/{filename}"  # 복수형 사용 (images, videos)
            )

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
