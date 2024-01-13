from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as lg_desc:
    long_description = lg_desc.read()

setup(
    name="py_version_tracker",
    version="0.0.1",
    author="Yousef Abuzahrieh",
    author_email="yousefzahrieh17@gmail.com",
    description="PyVersionTracker is a Python utility for tracking and managing Python versions.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yousefabuz17/PyVersionTracker",
    download_url="https://github.com/yousefabuz17/PyVersionTracker.git",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    platforms=["Windows", "Linux", "MacOS"],
    license="Apache Software License",
    install_requires=['aiohttp~=3.9.0b0', 'beautifulsoup4~=4.12.2',
                    'setuptools~=68.2.2', 'pypistats~=1.5.0'],
    classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: Apache Software License", 
    "Operating System :: OS Independent",
    ],
)
