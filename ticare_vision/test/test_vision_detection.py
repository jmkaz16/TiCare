"""Validation tests for image processing and object-detection outputs."""

from types import SimpleNamespace

from conftest import FakeBridge, FakePublisher


class FakeBox:
    def __init__(self, class_id):
        self.cls = [class_id]


class FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes

    def plot(self):
        return "annotated_frame"


class FakeModel:
    def __init__(self, results, names=None):
        self.results = results
        self.names = names or {0: "bottle", 1: "mug", 2: "glasses"}
        self.predict_calls = []

    def predict(self, frame, conf, verbose):
        self.predict_calls.append((frame, conf, verbose))
        return self.results


def _patch_cv2_display(vision_module, monkeypatch):
    monkeypatch.setattr(vision_module.cv2, "imshow", lambda *args, **kwargs: None)
    monkeypatch.setattr(vision_module.cv2, "waitKey", lambda *args, **kwargs: 1)
    monkeypatch.setattr(vision_module.cv2, "destroyAllWindows", lambda: None)


def _configured_detection_node(vision_module, bare_vision_node, target="bottle"):
    node = bare_vision_node()
    node.current_state = vision_module.VisionState.BUSQUEDA_ACTIVA
    node.target_object = target
    node.bridge = FakeBridge(frame="cv_frame")
    node.pub_vis2com = FakePublisher()
    node.pub_vis2nav = FakePublisher()
    return node


def test_camera_callback_ignores_images_when_vision_is_not_active(
    vision_module, bare_vision_node
):
    """Verify that images do not trigger inference outside BUSQUEDA_ACTIVA."""

    node = bare_vision_node()
    node.current_state = vision_module.VisionState.ESPERANDO_OBJETO
    node.bridge = FakeBridge()
    node.model = FakeModel(results=[])

    node.camera_callback(SimpleNamespace())

    assert node.bridge.calls == []
    assert node.model.predict_calls == []


def test_target_detection_publishes_object_detected_to_com_and_nav(
    vision_module, bare_vision_node, monkeypatch
):
    """Validate the required output when the selected target is detected."""

    _patch_cv2_display(vision_module, monkeypatch)
    node = _configured_detection_node(vision_module, bare_vision_node, target="bottle")
    node.model = FakeModel(results=[FakeResult([FakeBox(0)])])

    node.camera_callback(SimpleNamespace())

    assert node.bridge.calls[0][1] == "bgr8"
    assert node.model.predict_calls == [("cv_frame", 0.6, False)]
    assert node.pub_vis2com.published == ["object_detected"]
    assert node.pub_vis2nav.published == ["object_detected"]
    assert node.current_state == vision_module.VisionState.VISION_DETENIDA


def test_non_target_detection_does_not_publish_or_stop_search(
    vision_module, bare_vision_node, monkeypatch
):
    """Verify that detecting another valid class does not finish the search."""

    _patch_cv2_display(vision_module, monkeypatch)
    node = _configured_detection_node(vision_module, bare_vision_node, target="glasses")
    node.model = FakeModel(results=[FakeResult([FakeBox(0)])])

    node.camera_callback(SimpleNamespace())

    assert node.pub_vis2com.published == []
    assert node.pub_vis2nav.published == []
    assert node.current_state == vision_module.VisionState.BUSQUEDA_ACTIVA


def test_image_conversion_error_is_handled_without_publishing(
    vision_module, bare_vision_node
):
    """Verify that a bad ROS image message does not crash the node."""

    node = _configured_detection_node(vision_module, bare_vision_node, target="bottle")
    node.bridge = FakeBridge(should_raise=True)
    node.model = FakeModel(results=[FakeResult([FakeBox(0)])])

    node.camera_callback(SimpleNamespace())

    assert node.model.predict_calls == []
    assert node.pub_vis2com.published == []
    assert node.pub_vis2nav.published == []
    assert node.current_state == vision_module.VisionState.BUSQUEDA_ACTIVA
