import re

# Read the file
with open('/home/lucas/ticare_ws/src/ticare_navigation/worlds/car.world', 'r') as f:
    content = f.read()

print(f"Content length: {len(content)}")
print(f"First 200 chars: {content[:200]}")

# Function to subtract 7.0 from y in pose
def modify_pose(match):
    parts = match.group(1).split()
    if len(parts) >= 6:
        x, y, z, roll, pitch, yaw = parts[:6]
        y_new = float(y) - 6.5
        x_new = float(x) + 1.0
        new_pose = f"{x_new} {y_new} {z} {roll} {pitch} {yaw}"
        return f"<pose>{new_pose}</pose>"
    return match.group(0)

# Regex to find <pose>...</pose>
pattern = r'<pose>([^<]+)</pose>'

# Replace all
new_content = re.sub(pattern, modify_pose, content)

includes = '    <include><uri>model://sun</uri></include>\n    <include><uri>model://ground_plane</uri></include>\n'

new_content = re.sub(r'(<world name="car">)', r'\1\n' + includes, new_content)

print(f"Replacements made: {len(re.findall(pattern, content))}")

# Write back
with open('/home/lucas/ticare_ws/src/ticare_navigation/worlds/car_shifted_final.world', 'w') as f:
    f.write(new_content)

print("Done")