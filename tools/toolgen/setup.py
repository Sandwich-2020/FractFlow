from setuptools import setup, find_packages

setup(
    name="toolgen",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "toolgen": ["templates/*.j2"],
    },
    install_requires=[
        "jinja2>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "toolgen=toolgen.cli:main",
        ],
    },
    author="FractFlow Team",
    author_email="team@fractflow.com",
    description="Tool Generator for FractFlow",
    keywords="template, codegen, fractflow",
    python_requires=">=3.8",
) 