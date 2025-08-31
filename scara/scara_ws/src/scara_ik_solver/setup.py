from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'scara_ik_solver'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
        (os.path.join('share', package_name, 'descriptions'), glob(os.path.join('descriptions', '*.[xml]*'))),
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*.[yaml]*'))),
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*.[rviz]*')))
     ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='AFMC',
    maintainer_email='andresfmc223@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            "scara_ik_solver = scara_ik_solver.scara_ik_solver:main"
        ],
    },
)
