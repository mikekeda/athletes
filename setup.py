from setuptools import setup, find_packages

setup(
    name='athletes',
    version='0.0.7',
    packages=find_packages(),
    install_requires=[
        'requests==2.21.0',
        'psycopg2==2.7.7',
        'psycopg2-binary==2.7.7',
        'gunicorn==19.9.0',
        'beautifulsoup4==4.7.1',
        'celery==4.2.1',
        'requests_oauthlib==1.2.0',
        'Pillow==5.4.1',
        'pytz==2018.9',
        'google-cloud-logging==1.10.0',
        'python-dateutil==2.7.5',
        'xmltodict==0.11.0',

        'django==2.1.5',
        'django-widget-tweaks==1.4.3',
        'django-easy-select2==1.5.5',
        'django-import-export',  # Installed from git due the the bug
        'django-debug-toolbar==1.11',
        'django-redis==4.10.0',
        'djangorestframework==3.9.1',
        'djangorestframework_simplejwt==3.3',
        'django-cors-headers==2.4.0'
        'dj-stripe==1.2.3'
    ],
    extras_require={
        "test": [
            'coverage==4.5.2',
        ]
    },
)
