from setuptools import find_packages, setup

package_name = 'ros2model'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/templates',
         ['templates/model.jinja', 'templates/node_model.jinja'])
    ],
    install_requires=['ros2cli'],
    zip_safe=True,
    maintainer='Christoph Hellmann Santos',
    maintainer_email='cmh@ipa.fraunhofer.de',
    description='Parser for interface specifications',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'ros2cli.command': [
            'model = ros2model.command.model:ModelCommand',
        ],
        'ros2cli.extension_point': [
            'ros2model.verb = ros2model.verb:VerbExtension',
        ],
        'ros2model.verb': [
            'interface_package = ros2model.verb.interface:InterfacePackageVerb',
            'running_node = ros2model.verb.running_node:RunningNodeVerb',
        ],
    }
)
