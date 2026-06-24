"""PyInstaller runtime hook: make OpenTelemetry entry_points discoverable.

In frozen PyInstaller environments, importlib.metadata.entry_points() returns
empty iterators. opentelemetry/context/__init__.py's _load_runtime_context()
relies on entry_points(group="opentelemetry_context") to find the contextvars
context — without it, it raises StopIteration.

This hook patches importlib.metadata.entry_points BEFORE any opentelemetry
module imports it (they do `from importlib.metadata import entry_points` at
module level, capturing the current reference).
"""
import importlib.metadata as _md

# All opentelemetry entry points, inlined from installed package metadata.
_ENTRIES: dict[str, dict[str, str]] = {
    "opentelemetry_context": {
        "contextvars_context": "opentelemetry.context.contextvars_context:ContextVarsRuntimeContext",
    },
    "opentelemetry_environment_variables": {
        "api": "opentelemetry.environment_variables",
    },
    "opentelemetry_meter_provider": {
        "default_meter_provider": "opentelemetry.metrics:NoOpMeterProvider",
    },
    "opentelemetry_propagator": {
        "baggage": "opentelemetry.baggage.propagation:W3CBaggagePropagator",
        "tracecontext": "opentelemetry.trace.propagation.tracecontext:TraceContextTextMapPropagator",
    },
    "opentelemetry_tracer_provider": {
        "default_tracer_provider": "opentelemetry.trace:NoOpTracerProvider",
    },
}


class _FakeEntryPoint:
    def __init__(self, name, module_path):
        self.name = name
        self.value = module_path
        self.group = ""

    def load(self):
        module_name, attr_name = self.module_path.split(":", 1)
        mod = __import__(module_name, fromlist=[attr_name])
        return getattr(mod, attr_name)


_original_entry_points = _md.entry_points


def _patched_entry_points(**kw):
    group, name = kw.get("group"), kw.get("name")
    if group in _ENTRIES:
        entries = _ENTRIES[group]
        if name is not None:
            if name in entries:
                return iter([_FakeEntryPoint(name, entries[name])])
            return iter([])
        return iter([_FakeEntryPoint(n, p) for n, p in entries.items()])
    return _original_entry_points(**kw)


_md.entry_points = _patched_entry_points
