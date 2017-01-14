from setuptools import setup
import glob
import os

setup(
    name='CL_Helper',
    version='1.0.0a1',
    description='A helper for a specific classifides service',
    author='Samuel Murphy',
    author_email='smurphy917@gmail.com',
    packages=['helper','helper_ui'],
    #libraries=[
    #    'selenium>=3.0',
    #    'flask>=0.11',
    #    'flask-script>=2.0',
    #    'schedule>=0.4.2',
    #    'requests>=2.9',
    #    'pyquery>=1.2',
    #    'apiclient>=1.0',
    #    'google-api-python-client>=1.5',
    #    'httplib2>=0.9'
    #],
    data_files={
        'helper/data': ['helper/data/cl_users.json','helper/data/posts.json']
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users",
        "Programming Language :: Python :: 3"
    ]
)