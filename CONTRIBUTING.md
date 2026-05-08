# Development Style & Coding Standards Guide

This document defines the coding standards, documentation practices, and workflow procedures for TiCare. All contributors are expected to follow these guidelines to ensure code consistency and maintainability.

## 1. Project Workflow & ROS 2 Architecture
### 1.1 Branching Strategy

To avoid conflicts, the project is divided into specialized teams. Each team must work on its designated branch:

- `navigation`: For path planning, SLAM, and localization.
- `vision`: For perception, object detection, and camera processing.
- `communication`: For user input and communication protocols.
    
**Merge Policy:** Merges to `main` will be handled via Pull Requests after peer review.

### 1.2 Package Naming & Documentation

- **Naming (REP 144):** Package names must be `snake_case`, lowercase, and prefixed with `ticare_` (e.g., `ticare_navigation`).
    
- **Architecture Spec:** Every package **must** include a `docs/architecture.md` file in English. This file must detail the nodes, interfaces (topics, services, actions), and dependencies.
    

### 1.3 Folder Structure

Each Python ROS 2 package must maintain a consistent layout:

```
├── docs/            # Documentation (architecture.md, diagrams)
└── ticare_package/
    ├── config/          # Static YAML parameters, controller configs
    ├── data/            # Dynamic mission data and runtime-modified files
    ├── launch/          # Python or XML launch files
    ├── maps/            # SLAM maps (.yaml, .pgm)
    ├── models/          # URDF, SDF, or mesh files
    ├── rviz/            # Rviz2 configuration files (.rviz)
    ├── scripts/         # Non-node python scripts (if any)
    ├── ticare_package/  # Python source code
    ├── worlds/          # Gazebo world files
    ├── package.xml      # Package metadata
    ├── setup.py         # Build instructions
    ├── setup.cfg        # Config instructions
    └── requirements.txt # External Python dependencies
```

**Note:** The filename and the node name defined in `setup.py` (entry_points) must be identical to help maintain clarity and consistency across the codebase.

## 2. Language and Naming Conventions

- **Primary Language:** All code, comments, documentation, and Git history must be in **English**.
- **Variable/Function/Module Names:** Use `snake_case`.
- **Class Names:** Use `PascalCase`.
- **Constants:** Use `UPPER_SNAKE_CASE`.

|**Entity**|**Convention**|**Example**|
|---|---|---|
|Classes|`PascalCase`|`LidarSensor`, `DataProcessor`|
|Functions / Methods|`snake_case`|`get_distance()`, `calculate_offset()`|
|Variables|`snake_case`|`current_pose`, `is_connected`|
|Files / Folders|`snake_case`|`motor_controller.py`|

## 3. Git Commit Guidelines

Commits should be concise and descriptive. We follow the **Imperative Mood** (as if giving an order to the codebase).
- **Format:** Start with a **Capital letter**. Do not end with a period.
- **Verb Tense:** Use **Infinitive/Imperative** (e.g., "Add", not "Added" or "Adds").
### Examples:

- `Add lidar calibration logic`
- `Update role permissions in README`
- `Fix memory leak in buffer allocation`
- `Implement launch configuration for ROS2`
- `Refactor transform tree broadcaster`

## 4. Python Coding Style

We follow the [ROS2 Python Style Guide](https://docs.ros.org/en/humble/The-ROS2-Project/Contributing/Code-Style-Language-Versions.html#python), which is based on **PEP 8**.
- **Line Length:** Maximum **100 characters**.
- **Quotes:** Use double quotes (") as the default. Single quotes are only used to avoid escaping.
- **Imports:** Only one import per line.
    - _Preferred:_
        ```Python
        from typing import Dict
        from typing import List
        ```
        
- **Indentation:** Use **4 spaces** per indentation level.
- **Comments:** Prefer putting comments **on the line before** the code they describe.
    - Use inline comments sparingly, only for very short explanations, separated by at least two spaces from the code.
        
**Note:** While ROS 2 recommends single quotes, TiCare adopts double quotes to align with standard Python formatting tools (Black).


## 5. Documentation (Google Style Docstrings)

Every class and public function must include a docstring following the **Google Style**. A docstring must contain:
1. **Summary:** A brief description of what the element does.
2. **Args:** Description of input parameters and their types.
3. **Returns:** Description of the return value and type (if applicable).
4. **Raises:** Any exceptions that might be intentionally thrown.

### Example Implementation:

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class DataProcessorNode(Node):
    """
    Processes incoming sensor data and republishes filtered results.

    Attributes:
        subscription (Subscription): Subscriber for the raw_data topic.
        publisher (Publisher): Publisher for the filtered_data topic.
    """

    def __init__(self):
        """Initialize the node, subscriber, and publisher."""
        super().__init__('data_processor_node')
        self.subscription = self.create_subscription(
            String,
            'raw_data',
            self.listener_callback,
            10
        )
        self.publisher = self.create_publisher(String, 'filtered_data', 10)

    def listener_callback(self, msg: String) -> None:
        """
        Callback for handling incoming String messages.

        Args:
            msg (String): The message received from the raw_data topic.
        """
        processed_text = self.filter_noise(msg.data)
        out_msg = String()
        out_msg.data = processed_text
        self.publisher.publish(out_msg)

    def filter_noise(self, text: str) -> str:
        """
        Applies a basic filtering algorithm to the input string.

        Args:
            text (str): The raw string data to be processed.

        Returns:
            str: The processed string without whitespace noise.
        """
        return text.strip().upper()

```


## 6. Environment Configuration (VSCode)

To ensure consistency, all team members should use the following `settings.json` configuration in VSCode. This uses **Black** as the default formatter.


```json
{
    "editor.tabSize": 4,
    "editor.insertSpaces": true,
    "editor.detectIndentation": false,
    "editor.formatOnSave": true,
    "editor.rulers": [100],
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit"
        }
    },
    "black-formatter.args": [
        "--line-length",
        "100",
    ]
}
```

