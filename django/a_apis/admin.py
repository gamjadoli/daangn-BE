from a_apis.models.product import Product, ProductImage
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

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="150" height="150" />', obj.image.url
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
        "status",
        "view_count",
        "refresh_at",
        "created_at",
    )

    list_filter = (
        "status",
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
                    "price",
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
        if obj.image:
            return format_html(
                '<img src="{}" width="150" height="150" />', obj.image.url
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
