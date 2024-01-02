#!/usr/bin/env python3


import ServiceDiscovery
import setuptools



if __name__ == '__main__':
    setuptools.setup(
        name = 'ServiceDiscovery',
        version = ServiceDiscovery.version,
        packages = ["ServiceDiscovery"],
        entry_points={
            'console_scripts': [
                'ServiceDiscoveryD=ServiceDiscovery.ServiceDiscoveryD:main',
                'ServiceDiscoveryC=ServiceDiscovery.ServiceDiscoveryC:main'
            ],
        },
        install_requires = [],
        author = "Javier Moreno Garcia",
        author_email = "jgmore@gmail.com",
        description = "",
        long_description_content_type = "text/markdown",
        long_description = "",
        url = "https://github.com/qeyup/ServiceDiscovery-python",
    )

