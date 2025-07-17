"""
Advanced Input Validation and Sanitization for Mental Health Agent
Protects against injection attacks, prompt injection, and malicious input.
"""

import re
import html
import bleach
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import hashlib
import magic
from urllib.parse import urlparse

from ..monitoring.logging_config import get_logger

logger = get_logger("security.input_validation")


class PromptInjectionDetector:
    """Detects and prevents prompt injection attacks."""
    
    def __init__(self):
        """Initialize prompt injection detector."""
        self.injection_patterns = [
            # Direct instruction injection
            r'(?i)\b(?:ignore|forget|disregard)\s+(?:previous|all|above|prior)\s+(?:instructions?|prompts?|rules?)\b',
            r'(?i)\b(?:new|different|alternative)\s+(?:instructions?|prompts?|rules?)\b',
            r'(?i)\bact\s+as\s+(?:a\s+)?(?:different|new|another)\b',
            r'(?i)\bpretend\s+(?:to\s+be|you\s+are)\b',
            r'(?i)\brole\s*[:=]\s*(?!patient|user)',
            
            # System prompt manipulation
            r'(?i)\bsystem\s*[:=]',
            r'(?i)\bassistant\s*[:=]',
            r'(?i)\buser\s*[:=]',
            r'(?i)\b(?:start|begin)\s+new\s+(?:conversation|session|chat)\b',
            
            # Jailbreak attempts
            r'(?i)\b(?:jailbreak|bypass|override|circumvent)\b',
            r'(?i)\bdo\s+anything\s+now\b',
            r'(?i)\bdan\s+mode\b',
            r'(?i)\bunrestricted\s+mode\b',
            
            # Code injection
            r'(?i)\b(?:execute|run|eval)\s*\(',
            r'(?i)\bimport\s+\w+',
            r'(?i)\b__\w+__\b',
            r'(?i)\bos\.\w+',
            r'(?i)\bsystem\s*\(',
            
            # Prompt leakage attempts
            r'(?i)\bshow\s+(?:me\s+)?(?:your|the)\s+(?:prompt|instructions?|rules?)\b',
            r'(?i)\bwhat\s+(?:are\s+)?(?:your|the)\s+(?:instructions?|rules?|guidelines?)\b',
            r'(?i)\brepeat\s+(?:your|the)\s+(?:prompt|instructions?)\b',
            
            # Delimiter confusion
            r'["""\']{3,}',
            r'---+',
            r'===+',
            r'\[INST\]|\[/INST\]',
            r'<\|.*?\|>',
        ]
        
        self.compiled_patterns = [re.compile(pattern) for pattern in self.injection_patterns]
    
    def detect_injection(self, text: str) -> Tuple[bool, List[str], float]:
        """
        Detect prompt injection attempts.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (is_injection, detected_patterns, confidence_score)
        """
        detected_patterns = []
        confidence = 0.0
        
        # Check against known patterns
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.findall(text)
            if matches:
                detected_patterns.append(f"Pattern {i+1}: {self.injection_patterns[i]}")
                confidence += 0.3
        
        # Additional heuristics
        
        # Check for excessive special characters
        special_char_ratio = len(re.findall(r'[^\w\s]', text)) / len(text) if text else 0
        if special_char_ratio > 0.3:
            detected_patterns.append("High special character ratio")
            confidence += 0.2
        
        # Check for multiple role definitions
        role_mentions = len(re.findall(r'(?i)\b(?:system|assistant|user|human|ai)\b', text))
        if role_mentions > 3:
            detected_patterns.append("Multiple role mentions")
            confidence += 0.2
        
        # Check for instruction-like language
        instruction_words = ['must', 'should', 'always', 'never', 'only', 'exactly', 'precisely']
        instruction_count = sum(1 for word in instruction_words if word in text.lower())
        if instruction_count > 3:
            detected_patterns.append("Instruction-like language")
            confidence += 0.1
        
        # Check for encoding attempts
        if any(encoding in text.lower() for encoding in ['base64', 'hex', 'unicode', 'ascii']):
            detected_patterns.append("Encoding references")
            confidence += 0.3
        
        is_injection = confidence >= 0.5
        
        if is_injection:
            logger.warning(f"Prompt injection detected", 
                         confidence=confidence, 
                         patterns=len(detected_patterns))
        
        return is_injection, detected_patterns, min(confidence, 1.0)


class InputSanitizer:
    """Sanitizes user input to prevent various attacks."""
    
    def __init__(self):
        """Initialize input sanitizer."""
        self.allowed_tags = ['b', 'i', 'em', 'strong', 'p', 'br']
        self.allowed_attributes = {}
        
        # File type validation
        self.allowed_file_types = {
            'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
            'audio': ['audio/mpeg', 'audio/wav', 'audio/ogg'],
            'document': ['application/pdf', 'text/plain']
        }
        
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def sanitize_text(self, text: str, allow_html: bool = False) -> str:
        """
        Sanitize text input.
        
        Args:
            text: Input text
            allow_html: Whether to allow safe HTML tags
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize unicode
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        if allow_html:
            # Use bleach to sanitize HTML
            text = bleach.clean(
                text,
                tags=self.allowed_tags,
                attributes=self.allowed_attributes,
                strip=True
            )
        else:
            # Escape HTML entities
            text = html.escape(text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit length
        if len(text) > 10000:  # 10k character limit
            text = text[:10000] + "..."
            logger.warning("Input truncated due to length limit")
        
        return text
    
    def validate_file_upload(self, file_data: bytes, filename: str, expected_type: str) -> Dict[str, Any]:
        """
        Validate uploaded file.
        
        Args:
            file_data: File content bytes
            filename: Original filename
            expected_type: Expected file type category
            
        Returns:
            Validation result
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'file_info': {}
        }
        
        try:
            # Check file size
            if len(file_data) > self.max_file_size:
                result['errors'].append(f"File too large: {len(file_data)} bytes")
                return result
            
            # Check file content type using python-magic
            mime_type = magic.from_buffer(file_data, mime=True)
            
            # Validate against expected type
            if expected_type not in self.allowed_file_types:
                result['errors'].append(f"Unsupported file type category: {expected_type}")
                return result
            
            if mime_type not in self.allowed_file_types[expected_type]:
                result['errors'].append(f"Invalid file type: {mime_type}")
                return result
            
            # Check filename
            if not self._validate_filename(filename):
                result['errors'].append("Invalid filename")
                return result
            
            # Scan for malicious content
            malware_check = self._scan_for_malware(file_data, mime_type)
            if not malware_check['safe']:
                result['errors'].extend(malware_check['threats'])
                return result
            
            result['valid'] = True
            result['file_info'] = {
                'mime_type': mime_type,
                'size': len(file_data),
                'filename': filename
            }
            
        except Exception as e:
            result['errors'].append(f"File validation error: {str(e)}")
            logger.error(f"File validation failed: {e}")
        
        return result
    
    def _validate_filename(self, filename: str) -> bool:
        """Validate filename for security."""
        if not filename or len(filename) > 255:
            return False
        
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check for dangerous extensions
        dangerous_extensions = [
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
            '.jar', '.php', '.asp', '.aspx', '.jsp', '.sh', '.ps1'
        ]
        
        filename_lower = filename.lower()
        if any(filename_lower.endswith(ext) for ext in dangerous_extensions):
            return False
        
        # Check for hidden files
        if filename.startswith('.'):
            return False
        
        return True
    
    def _scan_for_malware(self, file_data: bytes, mime_type: str) -> Dict[str, Any]:
        """Basic malware scanning."""
        result = {'safe': True, 'threats': []}
        
        # Check for embedded scripts in images
        if mime_type.startswith('image/'):
            # Look for script tags in image files
            if b'<script' in file_data.lower() or b'javascript:' in file_data.lower():
                result['safe'] = False
                result['threats'].append("Embedded script detected in image")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            b'eval(',
            b'exec(',
            b'system(',
            b'shell_exec(',
            b'<?php',
            b'<%',
            b'<script',
        ]
        
        for pattern in suspicious_patterns:
            if pattern in file_data.lower():
                result['safe'] = False
                result['threats'].append(f"Suspicious pattern detected: {pattern.decode('utf-8', errors='ignore')}")
        
        return result
    
    def validate_url(self, url: str) -> Dict[str, Any]:
        """Validate URL input."""
        result = {'valid': False, 'errors': []}
        
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                result['errors'].append("Invalid URL scheme")
                return result
            
            # Check for localhost/private IPs (SSRF protection)
            if parsed.hostname:
                import ipaddress
                try:
                    ip = ipaddress.ip_address(parsed.hostname)
                    if ip.is_private or ip.is_loopback:
                        result['errors'].append("Private/localhost URLs not allowed")
                        return result
                except ValueError:
                    # Not an IP address, check hostname
                    if parsed.hostname.lower() in ['localhost', '127.0.0.1', '0.0.0.0']:
                        result['errors'].append("Localhost URLs not allowed")
                        return result
            
            # Check URL length
            if len(url) > 2048:
                result['errors'].append("URL too long")
                return result
            
            result['valid'] = True
            
        except Exception as e:
            result['errors'].append(f"URL validation error: {str(e)}")
        
        return result


class RateLimitValidator:
    """Validates input processing rate limits."""
    
    def __init__(self):
        """Initialize rate limit validator."""
        self.request_counts = {}
        self.limits = {
            'text_input': {'requests': 100, 'window': 3600},  # 100 per hour
            'file_upload': {'requests': 10, 'window': 3600},   # 10 per hour
            'crisis_detection': {'requests': 50, 'window': 3600}  # 50 per hour
        }
    
    def check_rate_limit(self, identifier: str, input_type: str) -> Dict[str, Any]:
        """Check if request is within rate limits."""
        current_time = int(datetime.utcnow().timestamp())
        key = f"{identifier}:{input_type}"
        
        if key not in self.request_counts:
            self.request_counts[key] = []
        
        # Clean old requests
        window = self.limits[input_type]['window']
        self.request_counts[key] = [
            req_time for req_time in self.request_counts[key]
            if current_time - req_time < window
        ]
        
        # Check limit
        limit = self.limits[input_type]['requests']
        current_count = len(self.request_counts[key])
        
        if current_count >= limit:
            return {
                'allowed': False,
                'limit': limit,
                'current': current_count,
                'reset_time': current_time + window
            }
        
        # Add current request
        self.request_counts[key].append(current_time)
        
        return {
            'allowed': True,
            'limit': limit,
            'current': current_count + 1,
            'remaining': limit - current_count - 1
        }


# Global instances
prompt_injection_detector = PromptInjectionDetector()
input_sanitizer = InputSanitizer()
rate_limit_validator = RateLimitValidator()


def validate_user_input(
    text: str,
    user_id: str,
    input_type: str = 'text_input',
    allow_html: bool = False
) -> Dict[str, Any]:
    """
    Comprehensive input validation.
    
    Args:
        text: Input text
        user_id: User identifier
        input_type: Type of input for rate limiting
        allow_html: Whether to allow HTML
        
    Returns:
        Validation result
    """
    result = {
        'valid': True,
        'sanitized_text': '',
        'errors': [],
        'warnings': [],
        'security_flags': []
    }
    
    try:
        # Rate limiting check
        rate_check = rate_limit_validator.check_rate_limit(user_id, input_type)
        if not rate_check['allowed']:
            result['valid'] = False
            result['errors'].append("Rate limit exceeded")
            return result
        
        # Prompt injection detection
        is_injection, patterns, confidence = prompt_injection_detector.detect_injection(text)
        if is_injection:
            result['security_flags'].append({
                'type': 'prompt_injection',
                'confidence': confidence,
                'patterns': patterns
            })
            
            # For high confidence, block the input
            if confidence > 0.8:
                result['valid'] = False
                result['errors'].append("Potential security threat detected")
                return result
            else:
                result['warnings'].append("Potential prompt injection detected")
        
        # Sanitize input
        sanitized = input_sanitizer.sanitize_text(text, allow_html)
        result['sanitized_text'] = sanitized
        
        # Log security events
        if result['security_flags'] or result['warnings']:
            logger.warning("Input security flags detected",
                         user_id=user_id,
                         flags=len(result['security_flags']),
                         warnings=len(result['warnings']))
        
    except Exception as e:
        logger.error(f"Input validation failed: {e}")
        result['valid'] = False
        result['errors'].append("Validation error")
    
    return result
