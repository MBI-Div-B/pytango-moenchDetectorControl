from setuptools import setup

version = open("VERSION", encoding="utf-8").read()

setup(
    name="tangods_moenchcontrol",
    version=version,
    description="tango DeviceServer for control of moench detector ",
    author="Leonid Lunin",
    author_email="lunin.leonid@gmail.com",
    python_requires=">=3.10",
    entry_points={
        "console_scripts": ["MoenchDetectorControl = tangods_moenchcontrol:main"]
    },
    license="MIT",
    packages=["tangods_moenchcontrol"],
    package_data={"tangods_moenchcontrol": ["VERSION"]},
    data_files=[
        ("", ["VERSION"]),
    ],
    url="https://github.com/MBI-Div-B/pytango-moenchDetectorControl",
    keywords=[
        "tango device",
        "tango",
        "pytango",
        "moench",
    ],
)
