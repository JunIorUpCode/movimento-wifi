# Task 3: Structured Logging System - Implementation

## Summary

Implemented a comprehensive structured logging system with JSON format, log rotation, correlation IDs for event tracking, and automatic sanitization of sensitive data.

## Requirements Implemented

### Requirement 25.1: JSON Structured Logging
✅ Sistema usa logging estruturado em formato JSON com campos: timestamp, level, component, message, context

### Requirement 25.2: Configurable Log Levels
✅ Sistema tem níveis de log configuráveis: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Requirement 25.4: Log Rotation
✅ Sistema rotaciona logs automaticamente (máximo 10MB por arquivo, manter últimos 10 arquivos)

### Requirement 25.5: Correlation ID
✅ Sistema inclui correlation_id em logs relacionados ao mesmo evento

### Additional: Sensitive Data Sanitization
✅ Sistema implementa sanitização de dados sensíveis (passwords, tokens, emails, etc.)

## Implementation Details

### 1. StructuredLogger Class

Located in `backend/app/logging/structured_logger.py`

**Features:**
- JSON formatted logs with structured fields
- Automatic log rotation (10MB per file, 10 backup files)
- Correlation ID support for tracking related events
- Sensitive data sanitization
- Configurable log levels
- Both file and console output

**Usage:**
```python
from app.logging import StructuredLogger, get_logger

# Create logger
logger = StructuredLogger("my_module")

# Log with context
logger.info("User logged in", user_id=123, ip="192.168.1.1")

# Use correlation ID for related events
corr_id = logger.set_correlation_id()
logger.info("Processing started")
logger.info("Processing step 1")
logger.info("Processing completed")
logger.clear_correlation_id()

# Log errors with exception
try:
    risky_operation()
except Exception:
    logger.exception("Operation failed")
```

### 2. JSONFormatter

Custom formatter that outputs logs in JSON format:

```json
{
  "timestamp": "2024-01-15T10:30:00.123456+00:00",
  "level": "INFO",
  "component": "calibration_service",
  "message": "Calibration completed",
  "correlation_id": "abc-123-def-456",
  "context": {
    "mean_rssi": -45.2,
    "std_rssi": 2.3,
    "samples_count": 60
  },
  "location": {
    "file": "/path/to/file.py",
    "line": 123,
    "function": "calibrate"
  }
}
```

### 3. SensitiveDataSanitizer

Automatically sanitizes sensitive data from logs:

**Sanitized Patterns:**
- Passwords: `password=secret` → `password=***REDACTED***`
- Tokens: `token: abc123` → `token=***REDACTED***`
- API Keys: `api_key=xyz789` → `api_key=***REDACTED***`
- Emails: `user@example.com` → `***REDACTED***`
- Phone numbers: `555-123-4567` → `***REDACTED***`
- Credit cards: `1234-5678-9012-3456` → `***REDACTED***`

**Dictionary Sanitization:**
```python
data = {
    "username": "john",
    "password": "secret123",
    "token": "abc-xyz"
}
# Automatically sanitized to:
{
    "username": "john",
    "password": "***REDACTED***",
    "token": "***REDACTED***"
}
```

### 4. Log Rotation

Automatic rotation configured with:
- **Max file size:** 10MB (configurable)
- **Backup count:** 10 files (configurable)
- **Encoding:** UTF-8

Files are named:
- `wifisense.log` (current)
- `wifisense.log.1` (most recent backup)
- `wifisense.log.2`
- ...
- `wifisense.log.10` (oldest backup)

### 5. Correlation ID

Track related events across the system:

```python
logger = get_logger(__name__)

# Generate correlation ID
corr_id = logger.set_correlation_id()

# All subsequent logs will include this correlation_id
logger.info("Event 1")
logger.info("Event 2")
logger.info("Event 3")

# Clear when done
logger.clear_correlation_id()
```

All logs with the same correlation_id can be filtered and analyzed together.

### 6. Global Setup

Setup logging for the entire application:

```python
from app.logging import setup_logging

# Configure global logging
setup_logging(log_level="INFO", log_dir="logs")
```

## Testing

Comprehensive test suite in `backend/test_task3_structured_logging.py`:

**Test Coverage:**
- ✅ Sensitive data sanitization (passwords, tokens, emails, nested dicts)
- ✅ JSON format validation
- ✅ Correlation ID tracking
- ✅ Context data logging
- ✅ Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- ✅ Exception logging with traceback
- ✅ Location info (file, line, function)
- ✅ Log rotation on size limit
- ✅ Backup count enforcement
- ✅ Logger singleton pattern
- ✅ Integration scenarios (calibration, detection, error handling)

**Test Results:**
```
25 passed, 626 warnings in 1.10s
```

All tests pass successfully!

## Integration with Existing Code

The structured logger can be easily integrated into existing services:

```python
# In calibration_service.py
from app.logging import get_logger

logger = get_logger(__name__)

class CalibrationService:
    def start_calibration(self):
        corr_id = logger.set_correlation_id()
        logger.info("Calibration started", duration=60, profile="default")
        
        try:
            # ... calibration logic ...
            logger.info("Calibration completed", 
                       mean_rssi=-45.2,
                       samples_count=60)
        except Exception as e:
            logger.exception("Calibration failed")
        finally:
            logger.clear_correlation_id()
```

## Files Created

1. `backend/app/logging/__init__.py` - Module exports
2. `backend/app/logging/structured_logger.py` - Main implementation
3. `backend/test_task3_structured_logging.py` - Comprehensive test suite
4. `backend/TASK_3_IMPLEMENTATION.md` - This documentation

## Next Steps

To use the structured logging system:

1. Import the logger in your modules:
   ```python
   from app.logging import get_logger
   logger = get_logger(__name__)
   ```

2. Replace existing logging calls with structured logger:
   ```python
   # Old
   import logging
   logging.info("User logged in")
   
   # New
   logger.info("User logged in", user_id=123, action="login")
   ```

3. Use correlation IDs for tracking related events:
   ```python
   corr_id = logger.set_correlation_id()
   # ... multiple related operations ...
   logger.clear_correlation_id()
   ```

4. Logs will be automatically written to `logs/wifisense.log` with rotation

## Benefits

- **Structured Data:** Easy to parse and analyze logs programmatically
- **Security:** Automatic sanitization of sensitive data
- **Traceability:** Correlation IDs link related events
- **Scalability:** Automatic log rotation prevents disk space issues
- **Debugging:** Rich context and location information
- **Compliance:** Structured format suitable for log aggregation tools
