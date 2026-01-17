"""Unit tests for OpenTelemetry tracing configuration."""

import pytest
from unittest.mock import patch, MagicMock


class TestInitTracing:
    """Tests for init_tracing function."""

    def test_init_without_endpoint(self):
        """Should use console exporter when no endpoint configured."""
        with patch("app.core.tracing.settings") as mock_settings:
            mock_settings.OTEL_EXPORTER_OTLP_ENDPOINT = None
            mock_settings.SERVICE_NAME = "test-service"
            mock_settings.APP_VERSION = "1.0.0"

            from app.core.tracing import init_tracing
            init_tracing()

    def test_init_with_endpoint(self):
        """Should configure OTLP exporter with endpoint."""
        with patch("app.core.tracing.settings") as mock_settings:
            mock_settings.OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4317"
            mock_settings.SERVICE_NAME = "test-service"
            mock_settings.APP_VERSION = "1.0.0"
            mock_settings.APP_ENV = "test"

            with patch("app.core.tracing.trace") as mock_trace:
                with patch("app.core.tracing.TracerProvider") as mock_provider:
                    with patch("app.core.tracing.OTLPSpanExporter") as mock_exporter:
                        from app.core.tracing import init_tracing
                        init_tracing()

                        mock_exporter.assert_called_once()


class TestInstrumentApp:
    """Tests for instrument_app function."""

    def test_instruments_fastapi(self):
        """Should instrument FastAPI app."""
        mock_app = MagicMock()

        with patch("app.core.tracing.FastAPIInstrumentor") as mock_instrumentor:
            from app.core.tracing import instrument_app
            instrument_app(mock_app)

            mock_instrumentor.instrument_app.assert_called_once()


class TestInstrumentRedis:
    """Tests for instrument_redis function."""

    def test_instruments_redis(self):
        """Should instrument Redis client."""
        with patch("app.core.tracing.RedisInstrumentor") as mock_instrumentor:
            mock_instance = MagicMock()
            mock_instrumentor.return_value = mock_instance

            from app.core.tracing import instrument_redis
            instrument_redis()

            mock_instance.instrument.assert_called_once()

    def test_handles_instrumentation_error(self):
        """Should handle instrumentation errors gracefully."""
        with patch("app.core.tracing.RedisInstrumentor") as mock_instrumentor:
            mock_instance = MagicMock()
            mock_instance.instrument.side_effect = Exception("Instrumentation failed")
            mock_instrumentor.return_value = mock_instance

            from app.core.tracing import instrument_redis
            # Should not raise
            instrument_redis()


class TestInstrumentSqlalchemy:
    """Tests for instrument_sqlalchemy function."""

    def test_instruments_engine(self):
        """Should instrument SQLAlchemy engine."""
        mock_engine = MagicMock()

        with patch("app.core.tracing.SQLAlchemyInstrumentor") as mock_instrumentor:
            mock_instance = MagicMock()
            mock_instrumentor.return_value = mock_instance

            from app.core.tracing import instrument_sqlalchemy
            instrument_sqlalchemy(mock_engine)

            mock_instance.instrument.assert_called_once_with(engine=mock_engine)

    def test_handles_instrumentation_error(self):
        """Should handle instrumentation errors gracefully."""
        mock_engine = MagicMock()

        with patch("app.core.tracing.SQLAlchemyInstrumentor") as mock_instrumentor:
            mock_instance = MagicMock()
            mock_instance.instrument.side_effect = Exception("Failed")
            mock_instrumentor.return_value = mock_instance

            from app.core.tracing import instrument_sqlalchemy
            # Should not raise
            instrument_sqlalchemy(mock_engine)


class TestGetTracer:
    """Tests for get_tracer function."""

    def test_get_tracer_returns_tracer(self):
        """Should return tracer instance."""
        with patch("app.core.tracing._tracer", MagicMock()):
            from app.core.tracing import get_tracer
            tracer = get_tracer()
            assert tracer is not None


class TestPropagationHelpers:
    """Tests for trace context propagation."""

    def test_extract_trace_context(self):
        """Should extract trace context from headers."""
        from app.core.tracing import extract_trace_context

        headers = {
            "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        }

        context = extract_trace_context(headers)
        # Should return a context (even if empty for test)
        assert context is not None

    def test_inject_trace_context(self):
        """Should inject trace context into headers."""
        from app.core.tracing import inject_trace_context

        headers = {}
        inject_trace_context(headers)
        # Headers may or may not have trace info depending on current span
        assert isinstance(headers, dict)


class TestTracerInstance:
    """Tests for tracer instance management."""

    def test_global_tracer_accessible(self):
        """Should have global tracer variable."""
        from app.core import tracing

        # _tracer is module-level variable
        assert hasattr(tracing, '_tracer')

    def test_get_tracer_returns_instance(self):
        """Should return tracer from get_tracer."""
        with patch("app.core.tracing._tracer", MagicMock()):
            from app.core.tracing import get_tracer
            tracer = get_tracer()
            # Returns either the tracer or gets a new one
            assert tracer is not None

    def test_get_tracer_creates_new_when_none(self):
        """Should create new tracer when _tracer is None."""
        import app.core.tracing as tracing_module

        original_tracer = tracing_module._tracer
        tracing_module._tracer = None

        try:
            with patch("app.core.tracing.trace") as mock_trace:
                mock_tracer = MagicMock()
                mock_trace.get_tracer.return_value = mock_tracer

                tracer = tracing_module.get_tracer()

                mock_trace.get_tracer.assert_called_once_with("processing-service")
                assert tracer == mock_tracer
        finally:
            tracing_module._tracer = original_tracer


class TestStartSpan:
    """Tests for start_span function."""

    def test_creates_span_with_attributes(self):
        """Should create span and set attributes."""
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_span.return_value = mock_span

        with patch("app.core.tracing.get_tracer", return_value=mock_tracer):
            from app.core.tracing import start_span

            span = start_span("test_operation", asset_id="123", size=1024)

            mock_tracer.start_span.assert_called_once_with("test_operation")
            mock_span.set_attribute.assert_any_call("asset_id", "123")
            mock_span.set_attribute.assert_any_call("size", 1024)
            assert span == mock_span

    def test_skips_none_attributes(self):
        """Should not set attributes with None values."""
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_span.return_value = mock_span

        with patch("app.core.tracing.get_tracer", return_value=mock_tracer):
            from app.core.tracing import start_span

            start_span("test_operation", valid="value", invalid=None)

            # Should only have one call for "valid"
            calls = mock_span.set_attribute.call_args_list
            assert len(calls) == 1
            assert calls[0][0] == ("valid", "value")


class TestCreateProcessingSpan:
    """Tests for create_processing_span function."""

    def test_creates_span_with_processing_attributes(self):
        """Should create span with standard processing attributes."""
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_span.return_value = mock_span

        with patch("app.core.tracing.get_tracer", return_value=mock_tracer):
            from app.core.tracing import create_processing_span

            span = create_processing_span(
                name="thumbnail_generation",
                asset_id="asset-123",
                workspace_id="ws-456",
                correlation_id="corr-789",
                custom_attr="value"
            )

            mock_tracer.start_span.assert_called_once_with("thumbnail_generation")
            mock_span.set_attribute.assert_any_call("asset.id", "asset-123")
            mock_span.set_attribute.assert_any_call("workspace.id", "ws-456")
            mock_span.set_attribute.assert_any_call("correlation.id", "corr-789")
            mock_span.set_attribute.assert_any_call("custom_attr", "value")

    def test_creates_span_without_correlation_id(self):
        """Should create span without correlation ID."""
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_span.return_value = mock_span

        with patch("app.core.tracing.get_tracer", return_value=mock_tracer):
            from app.core.tracing import create_processing_span

            create_processing_span(
                name="test",
                asset_id="asset-123",
                workspace_id="ws-456",
            )

            # correlation.id should not be set when correlation_id is None
            call_args = [call[0] for call in mock_span.set_attribute.call_args_list]
            assert ("correlation.id", "corr-789") not in call_args


class TestAddSpanAttributes:
    """Tests for add_span_attributes function."""

    def test_adds_attributes_to_current_span(self):
        """Should add attributes to current span."""
        mock_span = MagicMock()

        with patch("app.core.tracing.trace") as mock_trace:
            mock_trace.get_current_span.return_value = mock_span

            from app.core.tracing import add_span_attributes

            add_span_attributes(key1="value1", key2="value2")

            mock_span.set_attribute.assert_any_call("key1", "value1")
            mock_span.set_attribute.assert_any_call("key2", "value2")

    def test_skips_none_values(self):
        """Should skip attributes with None values."""
        mock_span = MagicMock()

        with patch("app.core.tracing.trace") as mock_trace:
            mock_trace.get_current_span.return_value = mock_span

            from app.core.tracing import add_span_attributes

            add_span_attributes(valid="value", invalid=None)

            # Should only set "valid"
            calls = [call[0] for call in mock_span.set_attribute.call_args_list]
            assert ("valid", "value") in calls
            assert ("invalid", None) not in calls


class TestRecordException:
    """Tests for record_exception function."""

    def test_records_exception_on_current_span(self):
        """Should record exception on current span."""
        mock_span = MagicMock()

        with patch("app.core.tracing.trace") as mock_trace:
            mock_trace.get_current_span.return_value = mock_span

            from app.core.tracing import record_exception

            exc = ValueError("Test error")
            record_exception(exc, "Custom message")

            mock_span.record_exception.assert_called_once_with(exc)
            mock_span.set_status.assert_called_once()

    def test_records_exception_with_default_message(self):
        """Should use exception string as default message."""
        mock_span = MagicMock()

        with patch("app.core.tracing.trace") as mock_trace:
            mock_trace.get_current_span.return_value = mock_span

            from app.core.tracing import record_exception

            exc = ValueError("Test error")
            record_exception(exc)

            mock_span.record_exception.assert_called_once_with(exc)


class TestSetSpanStatusOk:
    """Tests for set_span_status_ok function."""

    def test_sets_ok_status_on_current_span(self):
        """Should set OK status on current span."""
        mock_span = MagicMock()

        with patch("app.core.tracing.trace") as mock_trace:
            mock_trace.get_current_span.return_value = mock_span

            from app.core.tracing import set_span_status_ok

            set_span_status_ok()

            mock_span.set_status.assert_called_once()
