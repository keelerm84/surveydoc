from setuptools import setup

setup(
    name = 'surveydoc',
    version = '0.1.0',
    packages = ['surveydoc'],
    entry_points = {
        'console_scripts': [
            'surveydoc = surveydoc.__main__:main'
        ]
    }
)
