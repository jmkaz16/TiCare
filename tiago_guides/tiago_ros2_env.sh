#!/usr/bin/env bash

# TIAGo ROS 2 CycloneDDS environment setup
# Usage:
#   source ~/ticare_ws/src/tiago_guides/tiago_ros2_env.sh
#
# Important:
#   Must be sourced, not executed, otherwise exports will not remain in your shell.

ROBOT_IP="${TIAGO_IP:-10.42.0.1}"
ROS_DOMAIN="${TIAGO_DOMAIN_ID:-29}"
XML_PATH="$HOME/.ros/cyclonedds_tiago.xml"
LOG_PATH="/tmp/cyclonedds-tiago.log"

echo "=== TIAGo ROS 2 setup ==="
echo "Robot IP: $ROBOT_IP"
echo "ROS domain: $ROS_DOMAIN"
echo

# Check whether script is sourced.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "ERROR: This script must be sourced, not executed."
  echo "Use:"
  echo "  source ~/tiago_ros2_env.sh"
  exit 1
fi

# Avoid Conda interfering with ROS Python packages.
if [[ -n "${CONDA_PREFIX:-}" ]]; then
  echo "WARNING: Conda environment appears active: $CONDA_PREFIX"
  echo "Recommended:"
  echo "  conda deactivate"
  echo
fi

# Check ros2.
if ! command -v ros2 >/dev/null 2>&1; then
  echo "ERROR: ros2 command not found."
  echo "You probably need to source ROS first, e.g.:"
  echo "  source /opt/ros/humble/setup.bash"
  return 1
fi

echo "ros2: $(command -v ros2)"
echo "ROS_DISTRO: ${ROS_DISTRO:-<empty>}"

if [[ -z "${ROS_DISTRO:-}" ]]; then
  echo "ERROR: ROS_DISTRO is empty."
  echo "Run one of these first:"
  echo "  source /opt/ros/humble/setup.bash"
  echo "  source /opt/ros/jazzy/setup.bash"
  return 1
fi

# Check CycloneDDS RMW.
if ! ros2 pkg prefix rmw_cyclonedds_cpp >/dev/null 2>&1; then
  echo "ERROR: rmw_cyclonedds_cpp is not installed."
  echo "Install it with:"
  echo "  sudo apt update"
  echo "  sudo apt install ros-$ROS_DISTRO-rmw-cyclonedds-cpp"
  return 1
fi

echo "rmw_cyclonedds_cpp: $(ros2 pkg prefix rmw_cyclonedds_cpp)"
echo

# Check route.
ROUTE_OUTPUT="$(ip route get "$ROBOT_IP" 2>/dev/null)"
if [[ -z "$ROUTE_OUTPUT" ]]; then
  echo "ERROR: Cannot route to $ROBOT_IP."
  echo "Check that this computer is connected to the TIAGo network."
  return 1
fi

IFACE="$(echo "$ROUTE_OUTPUT" | awk '{for(i=1;i<=NF;i++) if($i=="dev") print $(i+1)}' | head -1)"
LOCAL_IP="$(echo "$ROUTE_OUTPUT" | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}' | head -1)"

echo "Route:"
echo "  $ROUTE_OUTPUT"
echo "Detected interface: $IFACE"
echo "Detected local IP:  $LOCAL_IP"
echo

if [[ -z "$IFACE" || -z "$LOCAL_IP" ]]; then
  echo "ERROR: Could not detect local interface or local IP."
  return 1
fi

# Ping robot.
echo "Checking reachability..."
if ping -c 2 -W 2 "$ROBOT_IP" >/dev/null 2>&1; then
  echo "Ping OK: $ROBOT_IP"
else
  echo "WARNING: Ping to $ROBOT_IP failed."
  echo "ROS 2 may still work if ICMP is blocked, but usually this means the network is not connected."
fi
echo

# Create CycloneDDS XML.
mkdir -p "$HOME/.ros"

if [[ -f "$XML_PATH" ]]; then
  BACKUP_PATH="${XML_PATH}.bak.$(date +%Y%m%d_%H%M%S)"
  cp "$XML_PATH" "$BACKUP_PATH"
  echo "Backed up existing XML to:"
  echo "  $BACKUP_PATH"
fi

cat > "$XML_PATH" <<XML
<?xml version="1.0" encoding="utf-8"?>
<CycloneDDS xmlns="https://cdds.io/config">
  <Domain Id="$ROS_DOMAIN">
    <General>
      <Interfaces>
        <NetworkInterface name="$IFACE" address="$LOCAL_IP" priority="100" multicast="false"/>
      </Interfaces>
      <ExternalNetworkAddress>$LOCAL_IP</ExternalNetworkAddress>
      <AllowMulticast>false</AllowMulticast>
    </General>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <Peers>
        <Peer Address="$ROBOT_IP"/>
      </Peers>
      <MaxAutoParticipantIndex>500</MaxAutoParticipantIndex>
    </Discovery>
    <Tracing>
      <Verbosity>config</Verbosity>
      <OutputFile>$LOG_PATH</OutputFile>
    </Tracing>
  </Domain>
</CycloneDDS>
XML

echo "Generated CycloneDDS config:"
echo "  $XML_PATH"
echo

# Export environment.
export ROS_DOMAIN_ID="$ROS_DOMAIN"
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI="file://$XML_PATH"
unset ROS_LOCALHOST_ONLY

echo "Environment loaded:"
echo "  ROS_DOMAIN_ID=$ROS_DOMAIN_ID"
echo "  RMW_IMPLEMENTATION=$RMW_IMPLEMENTATION"
echo "  CYCLONEDDS_URI=$CYCLONEDDS_URI"
echo "  ROS_LOCALHOST_ONLY=${ROS_LOCALHOST_ONLY:-<unset>}"
echo

# Warn about firewall.
if command -v ufw >/dev/null 2>&1; then
  UFW_STATUS="$(sudo ufw status 2>/dev/null | head -1 || true)"
  echo "UFW status: $UFW_STATUS"
  if echo "$UFW_STATUS" | grep -qi active; then
    echo "WARNING: ufw is active. If discovery fails, test with:"
    echo "  sudo ufw disable"
  fi
  echo
fi

# Stop daemon.
echo "Stopping ROS 2 daemon..."
ros2 daemon stop >/dev/null 2>&1 || true
pkill -f "_ros2_daemon" 2>/dev/null || true
pkill -f "ros2.*daemon" 2>/dev/null || true

# Clean old log.
rm -f "$LOG_PATH"

echo
echo "Test command:"
echo "  timeout 20s ros2 topic list --no-daemon --spin-time 15"
echo
echo "Running test..."
timeout 20s ros2 topic list --no-daemon --spin-time 15

RET=$?
echo

if [[ $RET -eq 0 ]]; then
  echo "Test finished."
  echo "If you see TIAGo topics such as /joint_states, /scan, /mobile_base_controller/odom, discovery is working."
elif [[ $RET -eq 124 ]]; then
  echo "WARNING: ros2 topic list timed out."
  echo "Check CycloneDDS log:"
  echo "  tail -120 $LOG_PATH"
else
  echo "WARNING: ros2 topic list exited with code $RET."
  echo "Check CycloneDDS log:"
  echo "  tail -120 $LOG_PATH"
fi

echo
echo "To test data:"
echo "  ros2 topic echo /joint_states sensor_msgs/msg/JointState --once"
echo
echo "To reuse later, run:"
echo "  source ~/ticare_ws/src/tiago_guides/tiago_ros2_env.sh
"
