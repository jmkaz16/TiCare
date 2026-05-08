#!/usr/bin/env bash

# Auto-detect TIAGo ROS 2 / Cyclone DDS environment.
#
# Usage:
#   source ~/ticare_ws/src/tiago_guides/tiago_ros2_auto_env.sh
#
# Optional overrides:
TIAGO_MODE=wired  #auto|wired|wifi Forces tiago to connect by wifi or wire the user requires
#   TIAGO_PREFER=wired|wifi
#   TIAGO_DOMAIN_ID=29
#   TIAGO_WIRED_IP=10.68.0.1
#   TIAGO_WIFI_IP=10.42.0.1
#   TIAGO_CYCLONEDDS_CONFIG=$HOME/.ros/cyclonedds_tiago_auto.xml
#   TIAGO_SKIP_PING=1
#
# This script must be sourced so the exported variables remain in the caller.

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "ERROR: source this script instead of executing it:"
  echo "  source ~/ticare_ws/src/tiago_guides/tiago_ros2_auto_env.sh"
  exit 1
fi

_tiago_log() {
  printf '[tiago-auto] %s\n' "$*"
}

_tiago_fail() {
  printf '[tiago-auto] ERROR: %s\n' "$*" >&2
  return 1
}

_tiago_parse_route_field() {
  local route="$1"
  local key="$2"
  awk -v key="$key" '{for (i = 1; i <= NF; i++) if ($i == key) {print $(i + 1); exit}}' <<<"$route"
}

_tiago_source_ros_if_needed() {
  if command -v ros2 >/dev/null 2>&1; then
    return 0
  fi

  if [[ -f /opt/ros/humble/setup.bash ]]; then
    # shellcheck disable=SC1091
    source /opt/ros/humble/setup.bash
  elif [[ -f /opt/ros/jazzy/setup.bash ]]; then
    # shellcheck disable=SC1091
    source /opt/ros/jazzy/setup.bash
  fi
}

_tiago_probe() {
  local mode="$1"
  local ip="$2"
  local route iface src

  route="$(ip route get "$ip" 2>/dev/null || true)"
  [[ -n "$route" ]] || return 1

  iface="$(_tiago_parse_route_field "$route" dev)"
  src="$(_tiago_parse_route_field "$route" src)"
  [[ -n "$iface" && -n "$src" ]] || return 1

  if [[ "${TIAGO_SKIP_PING:-0}" != "1" ]]; then
    ping -c 1 -W 1 -I "$iface" "$ip" >/dev/null 2>&1 || return 1
  fi

  TIAGO_MODE_DETECTED="$mode"
  TIAGO_IP="$ip"
  TIAGO_IFACE="$iface"
  TIAGO_LOCAL_IP="$src"
  TIAGO_ROUTE="$route"
  return 0
}

_tiago_select_network() {
  local requested="${TIAGO_MODE:-auto}"
  local prefer="${TIAGO_PREFER:-wired}"
  local wired_ip="${TIAGO_WIRED_IP:-10.68.0.1}"
  local wifi_ip="${TIAGO_WIFI_IP:-10.42.0.1}"

  case "$requested" in
    wired)
      _tiago_probe wired "$wired_ip" || _tiago_fail "wired TIAGo is not reachable at ${wired_ip}"
      ;;
    wifi|wi-fi)
      _tiago_probe wifi "$wifi_ip" || _tiago_fail "Wi-Fi TIAGo is not reachable at ${wifi_ip}"
      ;;
    auto)
      if [[ "$prefer" == "wifi" || "$prefer" == "wi-fi" ]]; then
        _tiago_probe wifi "$wifi_ip" || _tiago_probe wired "$wired_ip" || _tiago_fail "no reachable TIAGo network found"
      else
        _tiago_probe wired "$wired_ip" || _tiago_probe wifi "$wifi_ip" || _tiago_fail "no reachable TIAGo network found"
      fi
      ;;
    *)
      _tiago_fail "invalid TIAGO_MODE=${requested}; use auto, wired, or wifi"
      ;;
  esac
}

_tiago_write_cyclone_xml() {
  local config="${TIAGO_CYCLONEDDS_CONFIG:-$HOME/.ros/cyclonedds_tiago_auto.xml}"
  local log_file="${TIAGO_CYCLONE_LOG:-$HOME/.ros/log/cdds_tiago_auto.log}"

  mkdir -p "$(dirname "$config")" "$(dirname "$log_file")" || return 1

  cat >"$config" <<XML
<CycloneDDS>
  <Domain>
    <General>
      <AllowMulticast>false</AllowMulticast>
      <MaxMessageSize>1400B</MaxMessageSize>
      <Interfaces>
        <NetworkInterface name="${TIAGO_IFACE}" priority="1"/>
        <NetworkInterface name="lo" priority="0"/>
      </Interfaces>
    </General>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <Peers>
        <Peer Address="${TIAGO_IP}"/>
        <Peer Address="localhost"/>
      </Peers>
      <MaxAutoParticipantIndex>500</MaxAutoParticipantIndex>
    </Discovery>
    <Internal>
      <Watermarks>
        <WhcHigh>2000kB</WhcHigh>
      </Watermarks>
    </Internal>
    <Tracing>
      <Verbosity>config</Verbosity>
      <OutputFile>${log_file}</OutputFile>
    </Tracing>
  </Domain>
</CycloneDDS>
XML

  export TIAGO_CYCLONEDDS_CONFIG="$config"
}

_tiago_source_ros_if_needed

if ! command -v ip >/dev/null 2>&1; then
  _tiago_fail "ip command not found"
  return 1
fi

if ! command -v ping >/dev/null 2>&1; then
  _tiago_fail "ping command not found"
  return 1
fi

if ! command -v awk >/dev/null 2>&1; then
  _tiago_fail "awk command not found"
  return 1
fi

if ! command -v ros2 >/dev/null 2>&1; then
  _tiago_fail "ros2 command not found; source ROS first, for example: source /opt/ros/humble/setup.bash"
  return 1
fi

if command -v timeout >/dev/null 2>&1; then
  _tiago_rmw_check_cmd=(timeout 8s ros2 pkg prefix rmw_cyclonedds_cpp)
else
  _tiago_rmw_check_cmd=(ros2 pkg prefix rmw_cyclonedds_cpp)
fi

if ! "${_tiago_rmw_check_cmd[@]}" >/dev/null 2>&1; then
  _tiago_fail "rmw_cyclonedds_cpp is not visible; install ros-${ROS_DISTRO:-<distro>}-rmw-cyclonedds-cpp"
  unset _tiago_rmw_check_cmd
  return 1
fi
unset _tiago_rmw_check_cmd

_tiago_select_network || return 1
_tiago_write_cyclone_xml || return 1

export ROS_DOMAIN_ID="${TIAGO_DOMAIN_ID:-29}"
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI="file://${TIAGO_CYCLONEDDS_CONFIG}"
unset ROS_LOCALHOST_ONLY

if command -v timeout >/dev/null 2>&1; then
  timeout 5s ros2 daemon stop >/dev/null 2>&1 || true
else
  ros2 daemon stop >/dev/null 2>&1 || true
fi

_tiago_log "mode=${TIAGO_MODE_DETECTED}"
_tiago_log "robot=${TIAGO_IP}"
_tiago_log "interface=${TIAGO_IFACE}"
_tiago_log "local_ip=${TIAGO_LOCAL_IP}"
_tiago_log "route=${TIAGO_ROUTE}"
_tiago_log "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
_tiago_log "CYCLONEDDS_URI=${CYCLONEDDS_URI}"
_tiago_log "test: ros2 topic list --no-daemon --spin-time 20"

unset -f _tiago_log _tiago_fail _tiago_parse_route_field _tiago_source_ros_if_needed
unset -f _tiago_probe _tiago_select_network _tiago_write_cyclone_xml