from setuptools import setup

version = open("VERSION", encoding="utf-8").read()

setup(
    name="moenchcontroltangods",
    version=version,
    description="tango DeviceServer for control of moench detector ",
    author="Leonid Lunin",
    author_email="lunin.leonid@gmail.com",
    python_requires=">=3.10",
    entry_points={"console_scripts": ["MoenchControlServer = moenchzmqtangods:main"]},
    license="MIT",
    url="https://github.com/lrlunin/pytango-moenchZmqServer",
    keywords=[
        "tango device",
        "tango",
        "pytango",
        "moench",
    ],
)
