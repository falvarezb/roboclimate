import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="roboclimate",
    version="0.0.1",
    author="falvarezb",
    author_email="41089629+falvarezb@users.noreply.github.com",
    description="Evaluation of climate models accuracy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/falvarezb/roboclimate",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.6',
)