import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="zabbix_elasticsearch",
    version="0.2.1",
    author="Steve Simpson",
    author_email="stephen.simpson1991@gmail.com",
    description="Zabbix Monitoring for Elasticsearch",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/steve-simpson/zabbix_elasticsearch",
    packages=setuptools.find_packages(exclude=['tests']),
    data_files=[
        ('docs', ['docs/default.conf']),
    ],
    py_modules=['zabbix_elasticsearch'],
    install_requires=[
        'configparser>=4.0.2',
        'elasticsearch>=7.0.0',
        'urllib3>=1.25.6'
    ],
    entry_points={
        'console_scripts': [
            'zabbix_elasticsearch = zabbix_elasticsearch.zabbix_elasticsearch:main'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 3 - Alpha"
    ],
    python_requires='>=3.6',
    include_package_data=True
)