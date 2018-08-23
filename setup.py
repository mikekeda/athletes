from setuptools import setup, find_packages

setup(
    name='athletes',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'requests==2.19.1',
        'psycopg2==2.7.5',
        'psycopg2-binary==2.7.5',
        'django==2.1',
    ],
    extras_require={
        "test": [
            'coverage==4.5.1',
        ]
    },
)
