from setuptools import setup

setup(
    name="awsume-yubikey-plugin",
    version="1.2.4",
    description="Automates awsume MFA entry via YubiKey CLI.",
    entry_points={"awsume": ["yubikey = yubikey"]},
    author="Tony Spataro",
    author_email="pypi@tracker.xeger.net",
    url="https://github.com/xeger/awsume-yubikey-plugin",
    py_modules=["yubikey"],
)
