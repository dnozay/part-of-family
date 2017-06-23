from pip.req import parse_requirements
import setuptools


# Filters out relative/local requirements (i.e. ../lib/utils)
remote_requirements = '\n'.join(str(r.req) for r in parse_requirements("requirements.txt", session='dummy') if r.req)

setuptools.setup(
    name='part-of-family',
    version='0.0.1',

    author='<PLACEHOLDER>',
    author_email='<PLACEHOLDER>',

    description='<PLACEHOLDER>',
    long_description=open('README.rst').read(),

    url='<PLACEHOLDER>',

    install_requires=remote_requirements,

    license='MIT',

    packages=setuptools.find_packages(),
    include_package_data=True,

    setup_requires=['setuptools-git'],

    # entry_points={
    #    'console_scripts': [
    #        'script_name = package.module:entry_callable',
    #    ],
    # },

    classifiers=[
      'Development Status :: 5 - Production/Stable',

      'Intended Audience :: Developers',
      'Topic :: Software Development :: <PLACEHOLDER SUB-TOPIC>',

      'License :: OSI Approved :: MIT License',

      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.6',
    ],

    keywords='<KEYWORDS>',
)
