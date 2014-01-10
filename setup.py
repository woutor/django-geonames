from setuptools import setup, find_packages
import os

import geonames

setup(
    name = 'django-geonames',
    version = geonames.__version__,
    packages = find_packages(),
    include_package_data = True,
    license = 'BSD License',
    description = 'A Django app to use the information available in http://www.geonames.org',
    url = 'https://github.com/chrisspen/django-geonames',
    author = 'Chris Spencer',
    author_email = 'chrisspen@gmail.com',
    zip_safe = False,
    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
