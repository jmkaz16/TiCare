"""Static verification of the ROS interfaces promised by the vision module."""

from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
VISION_NODE_SOURCE = PACKAGE_ROOT / "ticare_vision" / "vision_node.py"
LAUNCH_SOURCE = PACKAGE_ROOT / "launch" / "vision_launch.launch.py"
CONFIG_SOURCE = PACKAGE_ROOT / "config" / "vision_params.yaml"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_real_robot_topics_are_kept_in_the_vision_node_contract():
    """Verify that the node uses the agreed integration topics and messages."""

    source = _source(VISION_NODE_SOURCE)

    for topic in (
        "/com2vis",
        "/nav2vis",
        "/vis2com",
        "/vis2nav",
        "/head_front_camera/rgb/image_raw",
        "/head_controller/follow_joint_trajectory",
    ):
        assert topic in source

    for message in (
        "head_up",
        "head_down",
        "object_",
        "start_vis",
        "stop_vis",
        "PE",
        "object_detected",
    ):
        assert message in source


def test_camera_topic_is_subscribed_and_not_created_as_a_new_publisher():
    """Verify that the TIAGo camera topic is consumed, not re-published."""

    source_without_spaces = _source(VISION_NODE_SOURCE).replace(" ", "")

    assert 'create_subscription(Image,"/head_front_camera/rgb/image_raw"' in source_without_spaces
    assert 'create_publisher(Image,"/head_front_camera/rgb/image_raw"' not in source_without_spaces


def test_launch_and_config_files_keep_required_parameters():
    """Verify launch/config files expose the parameters used by the node."""

    launch_source = _source(LAUNCH_SOURCE)
    config_source = _source(CONFIG_SOURCE)

    assert 'executable="vision_node"' in launch_source
    assert "vision_params.yaml" in launch_source
    assert "confidence_threshold" in config_source
    assert "head_1_joint" in config_source
    assert "head_2_joint" in config_source
