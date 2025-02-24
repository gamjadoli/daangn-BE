from a_common.models import CommonModel

from django.db import models


class File(CommonModel):
    file = models.FileField(upload_to="files/%Y/%m/%d/", verbose_name="파일")
    size = models.BigIntegerField(verbose_name="파일 크기")
    type = models.CharField(max_length=50, verbose_name="파일 타입(확장자)")

    class Meta:
        db_table = "files"
        verbose_name = "파일"
        verbose_name_plural = "파일 목록"

    def __str__(self):
        return self.file.name
