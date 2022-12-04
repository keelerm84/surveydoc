from setuptools import find_packages, setup

__version__ = '0.2.0'

setup(
    name='surveydoc',
    version=__version__,
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'surveydoc=surveydoc.__main__:main'
        ]
    },
    install_requires=[
        'boto3',
        'click',
        'google-api-python-client',
        'google-auth-httplib2',
        'google-auth-oauthlib',
        'pandas',
        'plotly',
        'psutil',
        'progress',
        'tox',
    ],
)
