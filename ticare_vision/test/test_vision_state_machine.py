"""Verification tests for the TiCare vision state machine."""

from types import SimpleNamespace

from conftest import DummyCapture


def _msg(data):
    return SimpleNamespace(data=data)


def test_nominal_sequence_from_activation_to_deactivation(
    vision_module, bare_vision_node, monkeypatch
):
    """Validate the expected COM/NAV sequence used during the demo."""

    node = bare_vision_node()
    destroy_calls = []
    captures = []

    def fake_video_capture(*args, **kwargs):
        capture = DummyCapture(*args, **kwargs)
        captures.append(capture)
        return capture

    monkeypatch.setattr(vision_module.cv2, "VideoCapture", fake_video_capture)
    monkeypatch.setattr(vision_module.cv2, "destroyAllWindows", lambda: destroy_calls.append(True))

    node.com2vis_callback(_msg("head_up"))
    assert node.current_state == vision_module.VisionState.PREPARANDO_VISION
    assert node.move_head_calls == [0.0]

    node.com2vis_callback(_msg("object_bottle"))
    assert node.current_state == vision_module.VisionState.ESPERANDO_OBJETO
    assert node.target_object == "bottle"

    node.nav2vis_callback(_msg("start_vis"))
    assert node.current_state == vision_module.VisionState.BUSQUEDA_ACTIVA
    assert node.move_head_calls == [0.0, -0.5]
    assert len(captures) == 1
    assert captures[0].released is False

    node.nav2vis_callback(_msg("stop_vis"))
    assert node.current_state == vision_module.VisionState.VISION_DETENIDA
    assert node.move_head_calls == [0.0, -0.5, 0.0]
    assert captures[0].released is True
    assert destroy_calls == [True]

    node.com2vis_callback(_msg("head_down"))
    assert node.current_state == vision_module.VisionState.ESPERANDO_ORDEN
    assert node.move_head_calls == [0.0, -0.5, 0.0, -0.75]


def test_invalid_commands_do_not_change_state(vision_module, bare_vision_node):
    """Verify that unexpected messages are ignored safely."""

    node = bare_vision_node()

    node.com2vis_callback(_msg("object_bottle"))
    assert node.current_state == vision_module.VisionState.ESPERANDO_ORDEN
    assert node.target_object == ""
    assert node.move_head_calls == []

    node.nav2vis_callback(_msg("start_vis"))
    assert node.current_state == vision_module.VisionState.ESPERANDO_ORDEN
    assert node.move_head_calls == []


def test_emergency_command_can_be_received_from_com_or_nav(
    vision_module, bare_vision_node, monkeypatch
):
    """Verify that PE always sends the state machine to EMERGENCIA."""

    monkeypatch.setattr(vision_module.cv2, "destroyAllWindows", lambda: None)

    node_from_com = bare_vision_node()
    node_from_com.current_state = vision_module.VisionState.BUSQUEDA_ACTIVA
    node_from_com.cap = DummyCapture()
    node_from_com.com2vis_callback(_msg("PE"))
    assert node_from_com.current_state == vision_module.VisionState.EMERGENCIA
    assert node_from_com.cap.released is True

    node_from_nav = bare_vision_node()
    node_from_nav.current_state = vision_module.VisionState.ESPERANDO_OBJETO
    node_from_nav.nav2vis_callback(_msg("PE"))
    assert node_from_nav.current_state == vision_module.VisionState.EMERGENCIA
