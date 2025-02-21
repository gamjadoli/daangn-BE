from django.http import JsonResponse


class ProcessPUTPatchMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method in ("PUT", "PATCH")
            and request.content_type != "application/json"
        ):
            original_method = request.method
            request.method = "POST"
            request.META["REQUEST_METHOD"] = "POST"
            request._load_post_and_files()  # 이 부분이 중요합니다!
            request.META["REQUEST_METHOD"] = original_method
            request.method = original_method
        return self.get_response(request)
