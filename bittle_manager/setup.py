from setuptools import find_packages, setup

package_name = 'bittle_manager'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='catalina',
    maintainer_email='ketamoran@gmail.com',
    description='Gestor de estados del Bittle',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'state_machine = bittle_manager.state_system_machine:main',
        ],
    },
)
