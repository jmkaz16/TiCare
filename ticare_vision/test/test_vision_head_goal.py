"""Verification tests for the TIAGo head trajectory goal."""


class FakeActionClient:
    """Action client replacement that records goals instead of sending them."""

    def __init__(self, server_available=True):
        self.server_available = server_available
        self.wait_timeouts = []
        self.goals = []

    def wait_for_server(self, timeout_sec=None):
        self.wait_timeouts.append(timeout_sec)
        return self.server_available

    def send_goal_async(self, goal):
        self.goals.append(goal)
        return "fake_future"


def test_move_head_sends_expected_joint_trajectory(vision_module, bare_vision_node):
    """Verify joint names, target positions and movement duration."""

    node = bare_vision_node(stub_move_head=False)
    node.head_action_client = FakeActionClient(server_available=True)

    node.move_head(-0.75)

    assert node.head_action_client.wait_timeouts == [2.0]
    assert len(node.head_action_client.goals) == 1

    goal = node.head_action_client.goals[0]
    assert list(goal.trajectory.joint_names) == ["head_1_joint", "head_2_joint"]
    assert len(goal.trajectory.points) == 1

    point = goal.trajectory.points[0]
    assert list(point.positions) == [0.0, -0.75]
    assert point.time_from_start.sec == 2
    assert point.time_from_start.nanosec == 0


def test_move_head_does_not_send_goal_when_controller_is_unavailable(
    vision_module, bare_vision_node
):
    """Verify safe behavior if /head_controller/follow_joint_trajectory is absent."""

    node = bare_vision_node(stub_move_head=False)
    node.head_action_client = FakeActionClient(server_available=False)

    node.move_head(-0.5)

    assert node.head_action_client.wait_timeouts == [2.0]
    assert node.head_action_client.goals == []
    assert node.logger.warning_messages
