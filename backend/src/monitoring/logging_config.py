"""
Structured logging configuration for Mental Health Agent.
Provides secure logging with sensitive data filtering and GDPR/HIPAA compliance.
"""

import logging
import logging.config
import json
import re
import os
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


class SensitiveDataFilter(logging.Filter):
    """Filter to remove sensitive data from log records."""
    
    def __init__(self):
        super().__init__()
        
        # Patterns for sensitive data
        self.sensitive_patterns = [
            # API Keys and tokens
            (r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]+)', r'api_key: "[REDACTED]"'),
            (r'token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9._-]+)', r'token: "[REDACTED]"'),
            (r'bearer\s+([a-zA-Z0-9._-]+)', r'bearer [REDACTED]'),
            
            # Passwords
            (r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'password: "[REDACTED]"'),
            (r'passwd["\']?\s*[:=]\s*["\']?([^"\'\s]+)', r'passwd: "[REDACTED]"'),
            
            # Email addresses (partial redaction)
            (r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'\1***@\2'),
            
            # Phone numbers
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', r'[PHONE_REDACTED]'),
            
            # Social Security Numbers
            (r'\b\d{3}-\d{2}-\d{4}\b', r'[SSN_REDACTED]'),
            
            # Credit card numbers
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', r'[CARD_REDACTED]'),
            
            # IP addresses (partial redaction)
            (r'\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b', r'\1.\2.***.\4'),
            
            # Medical record numbers
            (r'mrn["\']?\s*[:=]\s*["\']?([a-zA-Z0-9]+)', r'mrn: "[REDACTED]"'),
            
            # Session IDs and UUIDs (partial redaction)
            (r'([a-f0-9]{8})-([a-f0-9]{4})-([a-f0-9]{4})-([a-f0-9]{4})-([a-f0-9]{12})', r'\1-****-****-****-\5'),
        ]
    
    def filter(self, record):
        """Filter sensitive data from log record."""
        if hasattr(record, 'msg'):
            record.msg = self._redact_sensitive_data(str(record.msg))
        
        if hasattr(record, 'args') and record.args:
            record.args = tuple(
                self._redact_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        
        return True
    
    def _redact_sensitive_data(self, text: str) -> str:
        """Redact sensitive data from text."""
        for pattern, replacement in self.sensitive_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': record.process,
            'thread_id': record.thread,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if enabled
        if self.include_extra:
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                              'filename', 'module', 'lineno', 'funcName', 'created',
                              'msecs', 'relativeCreated', 'thread', 'threadName',
                              'processName', 'process', 'getMessage', 'exc_info',
                              'exc_text', 'stack_info']:
                    log_entry[key] = value
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class MentalHealthLogger:
    """Custom logger for Mental Health Agent with security features."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.request_id = None
        self.user_id = None
        self.session_id = None
    
    def set_context(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Set logging context for request tracking."""
        self.request_id = request_id
        self.user_id = user_id
        self.session_id = session_id
    
    def _add_context(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        """Add context information to log extra."""
        context = extra.copy()
        
        if self.request_id:
            context['request_id'] = self.request_id
        if self.user_id:
            context['user_id'] = self.user_id
        if self.session_id:
            context['session_id'] = self.session_id
        
        return context
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        extra = self._add_context(kwargs)
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        extra = self._add_context(kwargs)
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        extra = self._add_context(kwargs)
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        extra = self._add_context(kwargs)
        self.logger.error(message, extra=extra)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        extra = self._add_context(kwargs)
        self.logger.critical(message, extra=extra)
    
    def safety_event(self, event_type: str, details: Dict[str, Any], **kwargs):
        """Log safety-related events."""
        extra = self._add_context(kwargs)
        extra.update({
            'event_type': 'safety',
            'safety_event_type': event_type,
            'safety_details': details
        })
        self.logger.warning(f"Safety event: {event_type}", extra=extra)
    
    def privacy_event(self, event_type: str, details: Dict[str, Any], **kwargs):
        """Log privacy-related events."""
        extra = self._add_context(kwargs)
        extra.update({
            'event_type': 'privacy',
            'privacy_event_type': event_type,
            'privacy_details': details
        })
        self.logger.warning(f"Privacy event: {event_type}", extra=extra)
    
    def audit_log(self, action: str, resource: str, details: Dict[str, Any], **kwargs):
        """Log audit events for compliance."""
        extra = self._add_context(kwargs)
        extra.update({
            'event_type': 'audit',
            'action': action,
            'resource': resource,
            'audit_details': details,
            'audit_timestamp': datetime.utcnow().isoformat()
        })
        self.logger.info(f"Audit: {action} on {resource}", extra=extra)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_json: bool = True,
    enable_sensitive_filter: bool = True
) -> None:
    """
    Setup logging configuration for Mental Health Agent.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        enable_console: Whether to enable console logging
        enable_json: Whether to use JSON formatting
        enable_sensitive_filter: Whether to filter sensitive data
    """
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    # Configure logging
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': StructuredFormatter,
                'include_extra': True
            },
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            }
        },
        'filters': {
            'sensitive_data': {
                '()': SensitiveDataFilter
            } if enable_sensitive_filter else {}
        },
        'handlers': {},
        'loggers': {
            '': {  # Root logger
                'level': log_level,
                'handlers': []
            },
            'mental_health_agent': {
                'level': log_level,
                'handlers': [],
                'propagate': False
            },
            'uvicorn': {
                'level': 'INFO',
                'handlers': [],
                'propagate': False
            },
            'sqlalchemy': {
                'level': 'WARNING',
                'handlers': [],
                'propagate': False
            }
        }
    }
    
    # Add console handler
    if enable_console:
        config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'json' if enable_json else 'standard',
            'stream': 'ext://sys.stdout'
        }
        
        if enable_sensitive_filter:
            config['handlers']['console']['filters'] = ['sensitive_data']
        
        # Add to all loggers
        for logger_name in config['loggers']:
            config['loggers'][logger_name]['handlers'].append('console')
    
    # Add file handler
    if log_file:
        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'json' if enable_json else 'standard',
            'filename': log_file,
            'maxBytes': 100 * 1024 * 1024,  # 100MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }
        
        if enable_sensitive_filter:
            config['handlers']['file']['filters'] = ['sensitive_data']
        
        # Add to all loggers
        for logger_name in config['loggers']:
            config['loggers'][logger_name]['handlers'].append('file')
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log configuration success
    logger = logging.getLogger('mental_health_agent.logging')
    logger.info(
        "Logging configured",
        extra={
            'log_level': log_level,
            'log_file': log_file,
            'enable_console': enable_console,
            'enable_json': enable_json,
            'enable_sensitive_filter': enable_sensitive_filter
        }
    )


def get_logger(name: str) -> MentalHealthLogger:
    """Get a Mental Health Agent logger instance."""
    return MentalHealthLogger(f"mental_health_agent.{name}")


# Default logger for the monitoring module
logger = get_logger('monitoring')
