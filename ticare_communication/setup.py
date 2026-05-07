import os
from glob import glob

from setuptools import find_packages, setup

package_name = "ticare_communication"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "data"), glob("data/*.wav")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Mario",
    maintainer_email="mario.guerra.castelo@alumnos.upm.es",
    description="TiCare Communication node",
    license="Apache-2.0",
    extras_require={
        "test": ["pytest"],
    },
    entry_points={
        "console_scripts": [
            "state_manager = ticare_communication.state_manager:main",
            "save_audio = ticare_communication.audio_saver:main",
            "lanza_subprocess = ticare_communication.lanza_subprocess:main",
        ],
    },
)
