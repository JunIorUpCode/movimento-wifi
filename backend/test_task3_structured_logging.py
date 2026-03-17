"""
Tests for Task 3: Structured Logging System

Tests the StructuredLogger implementation with JSON format, log rotation,
correlation IDs, and sensitive data sanitization.

**Validates: Requirements 25.1, 25.2, 25.4, 25.5**
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from app.logging import StructuredLogger, get_logger, setup_logging
from app.logging.structured_logger import SensitiveDataSanitizer


class TestSensitiveDataSanitizer:
    """Test sensitive data sanitization."""
    
    def test_sanitize_password_in_string(self):
        """Test password sanitization in strings."""
        text = "User login with password=secret123"
        result = SensitiveDataSanitizer.sanitize(text)
        assert "secret123" not in result
        assert "***REDACTED***" in result
    
    def test_sanitize_token_in_string(self):
        """Test token sanitization in strings."""
        text = "API token: abc123xyz"
        result = SensitiveDataSanitizer.sanitize(text)
        assert "abc123xyz" not in result
        assert "***REDACTED***" in result
    
    def test_sanitize_email(self):
        """Test email sanitization."""
        text = "Contact user@example.com for details"
        result = SensitiveDataSanitizer.sanitize(text)
        assert "user@example.com" not in result
        assert "***REDACTED***" in result
    
    def test_sanitize_dict_with_password(self):
        """Test dictionary sanitization with password field."""
        data = {"username": "john", "password": "secret123"}
        result = SensitiveDataSanitizer.sanitize(data)
        assert result["password"] == "***REDACTED***"
        assert result["username"] == "john"
    
    def test_sanitize_nested_dict(self):
        """Test nested dictionary sanitization."""
        data = {
            "user": {
                "name": "john",
                "credentials": {
                    "password": "secret",
                    "token": "abc123"
                }
            }
        }
        result = SensitiveDataSanitizer.sanitize(data)
        assert result["user"]["credentials"]["password"] == "***REDACTED***"
        assert result["user"]["credentials"]["token"] == "***REDACTED***"
        assert result["user"]["name"] == "john"


class TestStructuredLogger:
    """Test StructuredLogger functionality."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def logger(self, temp_log_dir):
        """Create logger instance."""
        logger = StructuredLogger("test_logger", log_dir=temp_log_dir)
        yield logger
        logger.close()  # Close handlers to release file locks
    
    def test_logger_creates_log_file(self, temp_log_dir, logger):
        """Test that logger creates log file."""
        logger.info("Test message")
        log_file = Path(temp_log_dir) / "wifisense.log"
        assert log_file.exists()
    
    def test_json_format(self, temp_log_dir, logger):
        """Test that logs are in JSON format."""
        logger.info("Test message", key="value")
        
        log_file = Path(temp_log_dir) / "wifisense.log"
        with open(log_file, 'r') as f:
            log_line = f.readline()
            log_data = json.loads(log_line)
        
        assert "timestamp" in log_data
        assert log_data["level"] == "INFO"
        assert log_data["component"] == "test_logger"
        assert log_data["message"] == "Test message"
    
    def test_correlation_id(self, temp_log_dir, logger):
        """Test correlation ID tracking."""
        corr_id = logger.set_correlation_id("test-correlation-123")
        logger.info("Test message")
        
        log_file = Path(temp_log_dir) / "wifisense.log"
        with open(log_file, 'r') as f:
            log_line = f.readline()
            log_data = json.loads(log_line)
        
        assert log_data["correlation_id"] == "test-correlation-123"
    
    def test_auto_generate_correlation_id(self, logger):
        """Test automatic correlation ID generation."""
        corr_id = logger.set_correlation_id()
        assert corr_id is not None
        assert len(corr_id) > 0
    
    def test_clear_correlation_id(self, temp_log_dir, logger):
        """Test clearing correlation ID."""
        logger.set_correlation_id("test-123")
        logger.clear_correlation_id()
        logger.info("Test message")
        
        log_file = Path(temp_log_dir) / "wifisense.log"
        with open(log_file, 'r') as f:
            log_line = f.readline()
            log_data = json.loads(log_line)
        
        assert log_data["correlation_id"] is None
    
    def test_context_data(self, temp_log_dir, logger):
        """Test logging with context data."""
        logger.info("Test message", user="john", action="login", count=5)
        
        log_file = Path(temp_log_dir) / "wifisense.log"
        with open(log_file, 'r') as f:
            log_line = f.readline()
            log_data = json.loads(log_line)
        
        assert "context" in log_data
        assert log_data["context"]["user"] == "john"
        assert log_data["context"]["action"] == "login"
        assert log_data["context"]["count"] == 5

    def test_sensitive_data_sanitization(self, temp_log_dir, logger):
        """Test that sensitive data is sanitized in logs."""
        logger.info("User login", password="secret123", token="abc-xyz-789")
        
        log_file = Path(temp_log_dir) / "wifisense.log"
        with open(log_file, 'r') as f:
            log_line = f.readline()
            log_data = json.loads(log_line)
        
        assert log_data["context"]["password"] == "***REDACTED***"
        assert log_data["context"]["token"] == "***REDACTED***"
    
    def test_log_levels(self, temp_log_dir, logger):
        """Test different log levels."""
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        log_file = Path(temp_log_dir) / "wifisense.log"
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Should have at least info, warning, error, critical (debug might be filtered)
        assert len(lines) >= 4
    
    def test_set_log_level(self, temp_log_dir, logger):
        """Test setting log level."""
        logger.set_level("DEBUG")
        logger.debug("Debug message")
        
        log_file = Path(temp_log_dir) / "wifisense.log"
        with open(log_file, 'r') as f:
            log_line = f.readline()
            log_data = json.loads(log_line)
        
        assert log_data["level"] == "DEBUG"
    
    def test_exception_logging(self, temp_log_dir, logger):
        """Test exception logging with traceback."""
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("An error occurred")
        
        log_file = Path(temp_log_dir) / "wifisense.log"
        with open(log_file, 'r') as f:
            log_line = f.readline()
            log_data = json.loads(log_line)
        
        assert "exception" in log_data
        assert "ValueError" in log_data["exception"]
        assert "Test exception" in log_data["exception"]
    
    def test_location_info(self, temp_log_dir, logger):
        """Test that location info is included."""
        logger.info("Test message")
        
        log_file = Path(temp_log_dir) / "wifisense.log"
        with open(log_file, 'r') as f:
            log_line = f.readline()
            log_data = json.loads(log_line)
        
        assert "location" in log_data
        assert "file" in log_data["location"]
        assert "line" in log_data["location"]
        assert "function" in log_data["location"]


class TestLogRotation:
    """Test log rotation functionality."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_log_rotation_on_size(self, temp_log_dir):
        """Test that logs rotate when reaching max size."""
        # Create logger with small max size (1KB)
        logger = StructuredLogger(
            "test_logger",
            log_dir=temp_log_dir,
            max_bytes=1024,
            backup_count=3
        )
        
        # Write enough logs to trigger rotation
        for i in range(100):
            logger.info(f"Test message {i}" * 10)
        
        logger.close()  # Close handlers before checking files
        
        log_dir = Path(temp_log_dir)
        log_files = list(log_dir.glob("wifisense.log*"))
        
        # Should have main log + at least one backup
        assert len(log_files) >= 2

    def test_backup_count_limit(self, temp_log_dir):
        """Test that backup count is respected."""
        # Create logger with 2 backups max
        logger = StructuredLogger(
            "test_logger",
            log_dir=temp_log_dir,
            max_bytes=500,  # Very small to force rotation
            backup_count=2
        )
        
        # Write many logs to trigger multiple rotations
        for i in range(200):
            logger.info(f"Test message {i}" * 20)
        
        logger.close()  # Close handlers before checking files
        
        log_dir = Path(temp_log_dir)
        log_files = list(log_dir.glob("wifisense.log*"))
        
        # Should have main log + max 2 backups = 3 files
        assert len(log_files) <= 3


class TestGetLogger:
    """Test get_logger function."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_get_logger_returns_same_instance(self, temp_log_dir):
        """Test that get_logger returns same instance for same name."""
        logger1 = get_logger("test_module", log_dir=temp_log_dir)
        logger2 = get_logger("test_module")
        
        assert logger1 is logger2
        logger1.close()  # Clean up
    
    def test_get_logger_different_names(self, temp_log_dir):
        """Test that different names return different loggers."""
        logger1 = get_logger("module1", log_dir=temp_log_dir)
        logger2 = get_logger("module2", log_dir=temp_log_dir)
        
        assert logger1 is not logger2
        logger1.close()
        logger2.close()  # Clean up


class TestSetupLogging:
    """Test setup_logging function."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_setup_logging_creates_directory(self, temp_log_dir):
        """Test that setup_logging creates log directory."""
        log_dir = Path(temp_log_dir) / "new_logs"
        setup_logging(log_dir=str(log_dir))
        
        assert log_dir.exists()
    
    def test_setup_logging_creates_log_file(self, temp_log_dir):
        """Test that setup_logging creates log file."""
        setup_logging(log_dir=temp_log_dir)
        
        import logging
        logger = logging.getLogger("test")
        logger.info("Test message")
        
        log_file = Path(temp_log_dir) / "wifisense.log"
        assert log_file.exists()


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_calibration_logging_scenario(self, temp_log_dir):
        """Test logging scenario for calibration process."""
        logger = StructuredLogger("calibration_service", log_dir=temp_log_dir)
        
        # Start calibration with correlation ID
        corr_id = logger.set_correlation_id()
        logger.info("Calibration started", duration=60, profile="default")
        
        # Log progress
        logger.info("Calibration progress", samples_collected=30, progress_percent=50.0)
        
        # Log completion
        logger.info("Calibration completed", 
                   mean_rssi=-45.2, 
                   std_rssi=2.3,
                   samples_count=60)
        
        logger.clear_correlation_id()
        logger.close()  # Close before reading file
        
        # Verify all logs have same correlation ID
        log_file = Path(temp_log_dir) / "wifisense.log"
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        for line in lines:
            log_data = json.loads(line)
            assert log_data["correlation_id"] == corr_id

    def test_detection_logging_scenario(self, temp_log_dir):
        """Test logging scenario for detection events."""
        logger = StructuredLogger("detection_service", log_dir=temp_log_dir)
        
        # Log detection event
        logger.info("Event detected",
                   event_type="fall_suspected",
                   confidence=0.85,
                   rssi=-52.3,
                   rate_of_change=15.2)
        
        # Log alert sent
        logger.info("Alert sent",
                   channel="telegram",
                   recipient="user123",
                   success=True)
        
        logger.close()  # Close before reading file
        
        log_file = Path(temp_log_dir) / "wifisense.log"
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        
        # Verify first log
        log1 = json.loads(lines[0])
        assert log1["message"] == "Event detected"
        assert log1["context"]["event_type"] == "fall_suspected"
        
        # Verify second log
        log2 = json.loads(lines[1])
        assert log2["message"] == "Alert sent"
        assert log2["context"]["channel"] == "telegram"
    
    def test_error_logging_scenario(self, temp_log_dir):
        """Test logging scenario for error handling."""
        logger = StructuredLogger("monitor_service", log_dir=temp_log_dir)
        
        # Log error with context
        logger.error("Signal capture failed",
                    provider="rssi_windows",
                    attempt=3,
                    error_code="TIMEOUT")
        
        # Log exception
        try:
            raise ConnectionError("Network unavailable")
        except ConnectionError:
            logger.exception("Provider connection failed")
        
        logger.close()  # Close before reading file
        
        log_file = Path(temp_log_dir) / "wifisense.log"
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        
        # Verify error log
        log1 = json.loads(lines[0])
        assert log1["level"] == "ERROR"
        assert log1["message"] == "Signal capture failed"
        
        # Verify exception log
        log2 = json.loads(lines[1])
        assert log2["level"] == "ERROR"
        assert "exception" in log2
        assert "ConnectionError" in log2["exception"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
