import logging

logger = logging.getLogger(__name__)

_SKIP_PREFIXES = ('/admin/', '/static/', '/media/', '/favicon')
_BOT_KEYWORDS  = ('bot', 'crawler', 'spider', 'slurp', 'wget', 'curl', 'python-requests')


class PageViewMiddleware:
    """
    Records a PageView row for every real GET 200 response.
    Skips admin, static files, AJAX requests, and common bots.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if self._should_log(request, response):
            self._record(request)
        return response

    def _should_log(self, request, response):
        if request.method != 'GET':
            return False
        if response.status_code != 200:
            return False
        for prefix in _SKIP_PREFIXES:
            if request.path.startswith(prefix):
                return False
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return False
        ua = request.META.get('HTTP_USER_AGENT', '').lower()
        if any(kw in ua for kw in _BOT_KEYWORDS):
            return False
        return True

    def _record(self, request):
        try:
            from .models import PageView
            if not request.session.session_key:
                request.session.create()
            PageView.objects.create(
                path=request.path,
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key or '',
            )
        except Exception:
            logger.exception("PageView logging failed")
