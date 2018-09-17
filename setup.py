from setuptools import setup, find_packages

setup(
    name='athletes',
    version='0.0.3',
    packages=find_packages(),
    install_requires=[
        'requests==2.19.1',
        'psycopg2==2.7.5',
        'psycopg2-binary==2.7.5',
        'gunicorn==19.9.0',
        'beautifulsoup4==4.6.3',
        'celery==4.2.1',
        'requests_oauthlib==1.0.0',
        'gevent==1.3.6',

        'django==2.1',
        'django-widget-tweaks==1.4.3',
        'django-easy-select2==1.5.5',
        'django-import-export',  # Installed from git due the the bug
        'django-debug-toolbar==1.10.1',
        'django-redis==4.9.0',
    ],
    extras_require={
        "test": [
            'coverage==4.5.1',
        ]
    },
)
