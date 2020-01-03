import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="garmin",
    version="0.1.0",
    author="Ron Klinkien",
    author_email="ron@cyberjunky.nl",
    description="Python API wrapper for Garmin Connect",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cyberjunky/garmin",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
