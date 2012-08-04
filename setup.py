from setuptools import setup, find_packages
import os

version = '0.1'

setup(name='collective.subscribe',
      version=version,
      description="Components relating principals/users to content items.",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Programming Language :: Python",
        "Framework :: ZODB",
        "Framework :: Zope3",
        "Framework :: Plone",
        "Intended Audience :: Developers",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        ],
      keywords='',
      author='Sean Upton',
      author_email='sean.upton@hsc.utah.edu',
      url='https://github.com/collective/collective.subscribe',
      license='MIT',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
