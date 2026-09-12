from collections import OrderedDict, deque
from time import monotonic

from starlette.datastructures import Headers
from starlette.responses import JSONResponse

from app.core.config import settings


class RequestSecurityMiddleware:
    """Enforce write boundaries before multipart parsing or password hashing."""

    def __init__(self, app, allowed_origins: list[str]):
        self.app = app
        self.allowed_origins = set(allowed_origins)
        self.auth_attempts: OrderedDict[str, deque[float]] = OrderedDict()

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] in {'GET', 'HEAD', 'OPTIONS'}:
            return await self.app(scope, receive, send)
        path = scope['path']
        if not path.startswith(settings.api_prefix + '/'):
            return await self.app(scope, receive, send)

        headers = Headers(scope=scope)
        origin = headers.get('origin')
        # CORS controls response access, not whether a cookie-authenticated write executes.
        if (origin is not None and origin not in self.allowed_origins) or (
            origin is None and headers.get('sec-fetch-site') in {'cross-site', 'same-site'}
        ):
            return await JSONResponse({'detail': 'Request origin is not allowed.'}, status_code=403)(scope, receive, send)

        if path in {f'{settings.api_prefix}/auth/login', f'{settings.api_prefix}/auth/register'}:
            now = monotonic()
            cutoff = now - 60
            while self.auth_attempts and next(iter(self.auth_attempts.values()))[-1] <= cutoff:
                self.auth_attempts.popitem(last=False)
            address = (scope.get('client') or ('unknown', 0))[0]
            attempts = self.auth_attempts.get(address)
            if attempts is None:
                if len(self.auth_attempts) >= 10_000:
                    return await self._throttled(scope, receive, send)
                attempts = deque()
                self.auth_attempts[address] = attempts
            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if len(attempts) >= settings.auth_requests_per_minute:
                return await self._throttled(scope, receive, send)
            attempts.append(now)
            self.auth_attempts.move_to_end(address)

        limit = settings.max_api_body_kb * 1024
        if path.rstrip('/') == f'{settings.api_prefix}/resumes':
            limit = settings.max_resume_size_mb * 1024 * 1024 + 64 * 1024
        length = headers.get('content-length')
        if length is not None:
            try:
                size = int(length)
                if size < 0:
                    raise ValueError
            except ValueError:
                return await JSONResponse({'detail': 'Invalid Content-Length.'}, status_code=400)(scope, receive, send)
            if size > limit:
                return await self._too_large(scope, receive, send)

        # Count actual bytes as well: Content-Length can be absent on streamed requests.
        body = bytearray()
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            chunk = message.get('body', b'')
            if len(body) + len(chunk) > limit:
                return await self._too_large(scope, receive, send)
            body.extend(chunk)
            if not message.get('more_body', False):
                break

        consumed = False

        async def replay_body():
            nonlocal consumed
            if consumed:
                return await receive()
            consumed = True
            return {'type': 'http.request', 'body': bytes(body), 'more_body': False}

        await self.app(scope, replay_body, send)

    async def _throttled(self, scope, receive, send):
        await JSONResponse(
            {'detail': 'Too many sign-in attempts. Please wait a minute and retry.'},
            status_code=429, headers={'Retry-After': '60'},
        )(scope, receive, send)

    async def _too_large(self, scope, receive, send):
        await JSONResponse({'detail': 'Request body is too large.'}, status_code=413)(scope, receive, send)
