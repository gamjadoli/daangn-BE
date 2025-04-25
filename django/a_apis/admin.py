from a_apis.models.chat import ChatMessage, ChatRoom, ChatRoomParticipant
from a_apis.models.product import InterestProduct, Product, ProductImage
from a_apis.models.region import (
    EupmyeondongRegion,
    SidoRegion,
    SigunguRegion,
    UserActivityRegion,
)

from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils.html import format_html


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    verbose_name = "상품 이미지"
    verbose_name_plural = "상품 이미지 목록"
    readonly_fields = ["image_preview"]
    raw_id_fields = ["file"]

    def image_preview(self, obj):
        if obj.file and hasattr(obj.file, "url"):
            return format_html(
                '<img src="{}" width="150" height="150" />', obj.file.url
            )
        return "이미지 없음"

    image_preview.short_description = "이미지 미리보기"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "user",
        "price",
        "trade_type",
        "status",
        "view_count",
        "refresh_at",
        "created_at",
    )

    list_filter = (
        "status",
        "trade_type",
        "created_at",
        "refresh_at",
    )

    search_fields = (
        "title",
        "description",
        "user__email",
        "user__nickname",
    )

    ordering = ("-refresh_at", "-created_at")

    readonly_fields = (
        "view_count",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "기본 정보",
            {
                "fields": (
                    "title",
                    "user",
                    "trade_type",
                    "price",
                    "accept_price_offer",
                    "status",
                )
            },
        ),
        (
            "상세 정보",
            {
                "fields": (
                    "description",
                    "view_count",
                )
            },
        ),
        (
            "위치 정보",
            {"fields": ("location_description",)},
        ),
        (
            "날짜 정보",
            {
                "fields": (
                    "refresh_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    inlines = [ProductImageInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "image_preview", "created_at")
    search_fields = ("product__title",)
    list_filter = ("created_at",)
    readonly_fields = ["image_preview"]

    def image_preview(self, obj):
        if obj.file and hasattr(obj.file, "url"):
            return format_html(
                '<img src="{}" width="150" height="150" />', obj.file.url
            )
        return "이미지 없음"

    image_preview.short_description = "이미지 미리보기"


@admin.register(SidoRegion)
class SidoRegionAdmin(GISModelAdmin):
    list_display = ("name", "code", "created_at", "updated_at")
    search_fields = ("name", "code")
    ordering = ("code",)


@admin.register(SigunguRegion)
class SigunguRegionAdmin(GISModelAdmin):
    list_display = ("name", "code", "sido", "created_at", "updated_at")
    search_fields = ("name", "code", "sido__name")
    list_filter = ("sido",)
    ordering = ("code",)
    autocomplete_fields = ["sido"]


@admin.register(EupmyeondongRegion)
class EupmyeondongRegionAdmin(GISModelAdmin):
    list_display = ("name", "code", "sigungu", "created_at", "updated_at")
    search_fields = ("name", "code", "sigungu__name", "sigungu__sido__name")
    list_filter = ("sigungu__sido",)
    ordering = ("code",)
    autocomplete_fields = ["sigungu"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("sigungu", "sigungu__sido")


@admin.register(UserActivityRegion)
class UserActivityRegionAdmin(GISModelAdmin):
    list_display = (
        "user",
        "get_region_name",
        "priority",
        "verified_at",
        "last_verified_at",
    )
    search_fields = (
        "user__email",
        "activity_area__name",
        "activity_area__sigungu__name",
        "activity_area__sigungu__sido__name",
    )
    list_filter = ("priority", "verified_at")
    ordering = ("user", "priority")
    raw_id_fields = ("user", "activity_area")

    def get_region_name(self, obj):
        return f"{obj.activity_area.sigungu.sido.name} {obj.activity_area.sigungu.name} {obj.activity_area.name}"

    get_region_name.short_description = "활동지역"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "user",
                "activity_area",
                "activity_area__sigungu",
                "activity_area__sigungu__sido",
            )
        )


@admin.register(InterestProduct)
class InterestProductAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    search_fields = ("user__email", "product__title")
    list_filter = ("created_at",)
    raw_id_fields = ("user", "product")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "product")


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "get_participants",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "created_at", "updated_at")
    search_fields = (
        "product__title",
        "participants__user__nickname",
        "participants__user__email",
    )
    readonly_fields = ("created_at", "updated_at")

    def get_participants(self, obj):
        participants = obj.participants.select_related("user").all()
        return ", ".join([p.user.nickname for p in participants])

    get_participants.short_description = "참여자"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("product")
            .prefetch_related("participants", "participants__user")
        )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "chat_room",
        "sender",
        "short_message",
        "is_deleted",
        "created_at",
    )
    list_filter = ("is_deleted", "created_at")
    search_fields = (
        "message",
        "sender__nickname",
        "sender__email",
        "chat_room__product__title",
    )
    readonly_fields = ("created_at", "updated_at")

    def short_message(self, obj):
        max_length = 30
        if len(obj.message) > max_length:
            return f"{obj.message[:max_length]}..."
        return obj.message

    short_message.short_description = "메시지"

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related("chat_room", "sender", "file")
        )


@admin.register(ChatRoomParticipant)
class ChatRoomParticipantAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "chat_room",
        "user",
        "is_active",
        "last_read_message_id",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("user__nickname", "user__email", "chat_room__product__title")
    readonly_fields = ("created_at", "updated_at")

    def last_read_message_id(self, obj):
        return obj.last_read_message.id if obj.last_read_message else "-"

    last_read_message_id.short_description = "마지막 읽은 메시지 ID"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("chat_room", "user", "last_read_message")
        )
