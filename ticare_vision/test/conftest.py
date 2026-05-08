"""Shared fixtures for the TiCare vision validation tests."""

import importlib
import sys
import types

import pytest


class FakeLogger:
    """Small logger replacement used by tests without starting a ROS node."""

    def __init__(self):
        self.info_messages = []
        self.warning_messages = []
        self.error_messages = []

    def info(self, message):
        self.info_messages.append(message)

    def warn(self, message):
        self.warning_messages.append(message)

    def warning(self, message):
        self.warning_messages.append(message)

    def error(self, message):
        self.error_messages.append(message)


class DummyCapture:
    """cv2.VideoCapture replacement that never accesses real hardware."""

    def __init__(self, *args, opened=True, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.opened = opened
        self.released = False
        self.properties = []

    def isOpened(self):
        return self.opened

    def release(self):
        self.released = True

    def set(self, prop, value):
        self.properties.append((prop, value))
        return True


class FakePublisher:
    """Publisher test double that stores the published message data."""

    def __init__(self):
        self.published = []

    def publish(self, msg):
        self.published.append(getattr(msg, "data", msg))


class FakeBridge:
    """CvBridge replacement configurable for success and failure paths."""

    def __init__(self, frame="frame", should_raise=False):
        self.frame = frame
        self.should_raise = should_raise
        self.calls = []

    def imgmsg_to_cv2(self, msg, desired_encoding="bgr8"):
        self.calls.append((msg, desired_encoding))
        if self.should_raise:
            raise RuntimeError("conversion failed")
        return self.frame


@pytest.fixture
def vision_module(monkeypatch):
    """Import the real vision node while replacing heavy YOLO loading."""

    fake_ultralytics = types.ModuleType("ultralytics")

    class FakeYOLO:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.names = {}

        def predict(self, *args, **kwargs):
            return []

    fake_ultralytics.YOLO = FakeYOLO
    monkeypatch.setitem(sys.modules, "ultralytics", fake_ultralytics)

    return importlib.import_module("ticare_vision.vision_node")


@pytest.fixture
def bare_vision_node(vision_module):
    """Create a VisionNode object without calling rclpy Node.__init__."""

    def _factory(stub_move_head=True):
        node = vision_module.VisionNode.__new__(vision_module.VisionNode)
        node.current_state = vision_module.VisionState.ESPERANDO_ORDEN
        node.target_object = ""
        node.conf_thresh = 0.6
        node.window_name = "test_window"
        node.cap = None
        node.logger = FakeLogger()
        node.get_logger = lambda: node.logger

        if stub_move_head:
            node.move_head_calls = []
            node.move_head = lambda tilt: node.move_head_calls.append(tilt)

        return node

    return _factory
