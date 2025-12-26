from setuptools import setup, find_packages

setup(
    name='nagatoro-yaml-editor',
    version='1.0.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'PyQt5>=5.15.0',
        'PyYAML>=5.4.0',
        'pytest>=6.0.0',
    ],
    python_requires='>=3.7',
)