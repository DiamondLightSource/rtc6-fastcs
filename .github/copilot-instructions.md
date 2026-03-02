# AI Coding Instructions for rtc6-fastcs

## Project Overview

**rtc6-fastcs** is a FastCS IOC (EPICS Input/Output Controller) wrapping the ScanLab RTC6 Ethernet laser controller. It combines Python (device layer, controllers) with C++ bindings (low-level hardware communication).

### Architecture Layers

- **Bindings Layer** (`src/rtc6_fastcs/bindings/`): C++ pybind11 wrappers around proprietary RTC6 library
- **Controller Layer** (`src/rtc6_fastcs/controller/`): FastCS SubControllers managing EPICS attributes and hardware commands
- **Device Layer** (`src/rtc6_fastcs/device.py`): Ophyd-async StandardReadable devices exposing EPICS signals
- **Planning Layer** (`src/rtc6_fastcs/cut_shapes.py`, `plan_stubs.py`): Bluesky plans for laser cut shapes

### Key Dependencies

- **fastcs ~0.8.0**: FastCS framework for IOC infrastructure
- **ophyd-async**: Async device abstraction for beamline hardware
- **bluesky**: Experimental orchestration and planning
- **pybind11**: C++ to Python bindings

## Build & Development Workflow

### C++ Bindings Updates

When modifying C++ bindings (rtc6_bindings.cpp/pyi), rebuild using:

```bash
cd src/rtc6_fastcs/bindings/build
cmake ..
make
cd ../../../..
pybind11-stubgen rtc6_fastcs.bindings.rtc6_bindings -o src
ruff format .
```

The stub generator creates `rtc6_bindings.pyi` (do NOT edit manually).

### Test Requirements

- Tests requiring proprietary RTC6 library are marked `@pytest.mark.needs_librtc6` - exclude with `-m "not needs_librtc6"`
- Run full suite via: `tox -p` (defined in pyproject.toml, runs pytest, lint, docs in parallel)
- Test utilities in `tests/conftest.py` (check for shared fixtures)

### Python Version Constraint

**Python 3.11 only** - fastcs doesn't work properly on 3.12 (fails silently). Locked in pyproject.toml.

## Core Patterns & Conventions

### EPICS Attributes & Handlers

Controllers use FastCS attribute system with custom handlers:

```python
class RtcControlSettings(ConnectedSubController):
    @dataclass
    class ControlSettingsHandler(Sender):
        cmd: Callable
        async def put(self, controller, attr, value):
            self.cmd(value)  # Custom logic when attribute written
```

SubControllers inherit `RtcConnection` via `ConnectedSubController` parent.

### Ophyd-Async Device Pattern

Devices wrap EPICS signals, exposing Bluesky-compatible interfaces:

```python
class Rtc6ControlSettings(StandardReadable):
    def __init__(self, prefix: str = "CONTROL:"):
        with self.add_children_as_readables():
            self.laser_mode = epics_signal_rw(str, prefix + "LaserMode")
```

Nested classes (e.g., `Rtc6List.AddArc`) mirror nested EPICS hierarchies.

### C++ Function Wrapping

Bindings expose low-level RTC6 API directly:

- `rtc6.connect()`, `rtc6.close()`, `rtc6.check_connection()`
- `rtc6.add_line_to(x, y)`, `rtc6.add_arc_to(x, y, angle)`
- `rtc6.get_card_info()` returns CardInfo dataclass
- `rtc6.get_last_error()` / `get_error_string()` for error handling

### Bluesky Plans

Cut shape execution via Bluesky plans using device `.trigger()`:

```python
def draw_polygon(rtc: Rtc6Eth, shape):
    # shape: list of (x, y, mark_enabled) tuples
    yield from bps.open_run()
    # ... add geometry to list, execute_list trigger
```

## Testing & Debugging

### Unit Test Organization

- `test_bindings.py`: Direct binding function tests (marked `needs_librtc6`)
- `test_cli.py`: CLI/import tests
- Fixtures in `conftest.py` - check before creating new ones

### Connection Testing

The README notes: `test_connect()` from `test_bindings.py` must pass for hardware integration.

### Type Checking

`pyright` in standard mode enabled; `reportMissingImports=false` (imported modules lack stubs).

## Common Tasks

### Adding Hardware Commands

1. Add C++ binding in `rtc6_bindings.cpp` with pybind11 definition
2. Update `rtc6_bindings.pyi` stub or regenerate with pybind11-stubgen
3. Create FastCS attribute + handler in `controller/rtc_controller.py`
4. Wrap in ophyd device in `device.py`

### Fixing EPICS Prefix Issues

Device classes use `prefix` parameter to match IOC naming. Check:

- IOC record naming vs device prefix in `__init__.py`
- FastCS controller attribute groups in `rtc_controller.py`

### Debugging Bindings

Cannot directly inspect C++ behavior from Python tests - use logging in C++ or test via EPICS PVs.

## Project References

- **Source**: https://github.com/dperl-dls/rtc6-fastcs
- **Container**: `ghcr.io/dperl-dls/rtc6-fastcs:latest`
- **RTC6 Manual**: Referenced in code comments (e.g., "manual page 314")
