from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse

# class PermissionDeniedCustom(PermissionDenied):
#     def __call__(self, request):
#         referer = request.META.get('HTTP_REFERER')
#         messages.error = "Bạn không có quyền truy cập trang này"
#         return redirect(reverse('blog:index') + '?error=permission_denied')

class CustomErrorMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code == 404:
            return handle_404_error(request)
        elif response.status_code == 403:
            return handle_permission_denied(request)
        if response.status_code >= 500:
            return handle_5xx_error(request, response.status_code)
        
        return response
    
def handle_404_error(request):
    error_message = "Không tìm thấy trang"
    context = {
        'status_code': 404,
        'error_message': error_message,
    }
    return render(request, 'error.html', context, status=404)

def handle_permission_denied(request):
    error_message = "Bạn không có quyền truy cập trang Web này"
    context = {
        'status_code': 403,
        'error_message': error_message,
    }
    return render(request, 'error.html', context, status=403)
    
def handle_5xx_error(request, status_code):
    error_message = "Lỗi máy chủ"
    context={
        'status_code': status_code,
        'error_message': error_message
    }
    return render(request, 'error.html', context, status=status_code)

