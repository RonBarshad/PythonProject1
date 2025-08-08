from __future__ import annotations

import contextvars
import logging

# Per-update/request context
request_id_ctx = contextvars.ContextVar('request_id', default='-')
user_id_ctx = contextvars.ContextVar('user_id', default='-')
telegram_id_ctx = contextvars.ContextVar('telegram_id', default='-')
username_ctx = contextvars.ContextVar('username', default='-')
app_user_id_ctx = contextvars.ContextVar('app_user_id', default='-')


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Inject context vars into every record
        record.request_id = request_id_ctx.get()
        record.user_id = user_id_ctx.get()
        record.telegram_id = telegram_id_ctx.get()
        record.username = username_ctx.get()
        record.app_user_id = app_user_id_ctx.get()
        # Optional fields used in some logs
        record.handler = getattr(record, 'handler', getattr(record, 'handler', None))
        record.ticker = getattr(record, 'ticker', getattr(record, 'ticker', None))
        record.op = getattr(record, 'op', getattr(record, 'op', None))
        record.table = getattr(record, 'table', getattr(record, 'table', None))
        record.duration_ms = getattr(record, 'duration_ms', getattr(record, 'duration_ms', None))
        return True


