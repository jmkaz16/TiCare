import os
from glob import glob

from setuptools import find_packages, setup
from glob import glob

package_name = "ticare_navigation"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "data"), glob("data/*.yaml")),
        (os.path.join("share", package_name, "data"), glob("data/*.txt")),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
        (os.path.join("share", package_name, "worlds"), glob("worlds/*.world")),
        (os.path.join("share", package_name, "maps"), glob("maps/*.yaml")),
        (os.path.join("share", package_name, "maps"), glob("maps/*.pgm")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="catalina",
    maintainer_email="ketamoran@gmail.com",
    description="Implementation of the navigation stack, pose recording, and state management.",
    license="Apache-2.0",
    extras_require={
        "test": [
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "nav_manager = ticare_navigation.nav_manager:main",
            "pose_recorder = ticare_navigation.pose_recorder:main",
        ],
    },
)
