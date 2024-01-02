#!/usr/bin/env python3


import ServiceDiscovery
import setuptools



if __name__ == '__main__':
    setuptools.setup(
        name = 'ServiceDiscovery',
        version = ServiceDiscovery.version,
        packages = ["."],
        data_files = [
            "__init__.py",
            "ServiceDiscovery.py"
        ],
        install_requires = [],
        author = "Javier Moreno Garcia",
        author_email = "jgmore@gmail.com",
        description = "",
        long_description_content_type = "text/markdown",
        long_description = "",
        url = "https://github.com/qeyup/ServiceDiscovery-python",
    )

