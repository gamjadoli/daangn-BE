from a_common.models import CommonModel

from django.db import models


class ChatRoom(CommonModel):
    """채팅방 모델"""

    class Status(models.TextChoices):
        ACTIVE = "active", "활성"
        INACTIVE = "inactive", "비활성"

    product = models.ForeignKey(
        "a_apis.Product",
        on_delete=models.CASCADE,
        related_name="chat_rooms",
        verbose_name="상품",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="채팅방 상태",
    )

    class Meta:
        db_table = "chat_rooms"
        verbose_name = "채팅방"
        verbose_name_plural = "채팅방 목록"
        ordering = ["-updated_at"]  # 최근 메시지가 있는 채팅방이 상단에 위치

    def __str__(self):
        return f"Chat for {self.product.title}"


class ChatRoomParticipant(CommonModel):
    """채팅방 참여자 모델"""

    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="participants",
        verbose_name="채팅방",
    )
    user = models.ForeignKey(
        "a_user.User",
        on_delete=models.CASCADE,
        related_name="chat_participations",
        verbose_name="사용자",
    )
    last_read_message = models.ForeignKey(
        "ChatMessage",
        on_delete=models.SET_NULL,
        related_name="read_by_participants",
        verbose_name="마지막으로 읽은 메시지",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True, verbose_name="참여 상태")

    class Meta:
        db_table = "chat_room_participants"
        verbose_name = "채팅방 참여자"
        verbose_name_plural = "채팅방 참여자 목록"
        unique_together = [
            "chat_room",
            "user",
        ]  # 한 채팅방에 동일 사용자 중복 참여 방지

    def __str__(self):
        return f"{self.user.nickname} in {self.chat_room}"


class ChatMessage(CommonModel):
    """채팅 메시지 모델"""

    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="채팅방",
    )
    sender = models.ForeignKey(
        "a_user.User",
        on_delete=models.CASCADE,
        related_name="sent_messages",
        verbose_name="발신자",
    )
    message = models.TextField(verbose_name="메시지 내용")
    file = models.ForeignKey(
        "a_apis.File",
        on_delete=models.SET_NULL,
        related_name="chat_messages",
        verbose_name="첨부파일",
        null=True,
        blank=True,
    )
    is_deleted = models.BooleanField(default=False, verbose_name="삭제 여부")

    class Meta:
        db_table = "chat_messages"
        verbose_name = "채팅 메시지"
        verbose_name_plural = "채팅 메시지 목록"
        ordering = ["created_at"]  # 시간순 정렬

    def __str__(self):
        preview = self.message[:20] + "..." if len(self.message) > 20 else self.message
        return f"{self.sender.nickname}: {preview}"
