from setuptools import setup, find_packages

setup(
    name="mediaunmasked",
    version="0.1.0",
    packages=find_packages(exclude=["tests*"]) + ["app"],  # Include app/ and mediaunmasked/
    package_dir={"app": "app"},  # Map app directory
    install_requires=[
        line.strip()
        for line in open("requirements.txt").readlines()
        if not line.startswith("#")
    ],
    include_package_data=True,
    python_requires=">=3.10",
)
