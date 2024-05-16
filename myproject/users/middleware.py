from django.utils.deprecation import MiddlewareMixin
import logging
from django.http import HttpResponseForbidden



logger = logging.getLogger(__name__)

class LogIPMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            ip_address = request.META.get('REMOTE_ADDR')
            username = request.user.username
            logger.info(f"User {username} logged in from IP address {ip_address}")

class IPControlMiddleware:
    BLOCKED_IPS = ['192.168.1.1','192.168.137.114',]  # Example list of blocked IPs

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
       
        if request.META.get('REMOTE_ADDR') in self.BLOCKED_IPS:
            return HttpResponseForbidden("Access Denied: Your IP address is not allowed to access this page.")

        response = self.get_response(request)
        return response