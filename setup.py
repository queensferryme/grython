from setuptools import setup

setup(
    name='grython',
    version='0.0.0',
    author='Queenferry',
    author_email='queensferry.me@gmail.com',
    description='Light weight python crawler framework',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    include_package_data=True,
    install_requires=[
        'bs4',
        'requests'
    ],
    packages=['grython'],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    )
)
