#!/usr/bin/env bash

FILE="pal_urdf_utils/urdf/laser/sick_tim571_laser.gazebo.xacro"

if [ -f "$FILE" ]; then
    sed -i 's/gpu_lidar/lidar/g' "$FILE"
    echo "Lidar fixed!"
else
    echo "Error: Could not find $FILE"
fi
