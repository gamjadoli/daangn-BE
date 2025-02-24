from a_apis.models.product import Product, ProductImage

from django.contrib import admin


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    verbose_name = "상품 이미지"
    verbose_name_plural = "상품 이미지 목록"


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
