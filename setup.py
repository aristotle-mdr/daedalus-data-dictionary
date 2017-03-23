import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-aristotle-daedalus-data-dictionary',
    version='0.1',
    packages=['daedalus_data_dictionary'],
    include_package_data=True,
    license='BSD Licence',
    description='',
    long_description=README,
    url='https://github.com/aristotle-mdr/aristotle-daedalus-data-dictionary',
    author='Samuel Spencer',
    author_email='sam@sqbl.org',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License', # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires = [
        'aristotle-metadata-registry>=1.4.0',
        'dill'
    ]

)
