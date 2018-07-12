import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGELOG.md')) as f:
    CHANGES = f.read()

import uwsgi_app

requires = [
    'SQLAlchemy',
    'six',
]

tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest',  # includes virtualenv
    'pytest-cov',
]

setup(name='uwsgi_app',
      version='.'.join([str(v) for v in uwsgi_app.__version__]),
      description='',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 3",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Topic :: Software Development :: Libraries",
          "Topic :: Utilities",
      ],
      author='TerryXi',
      author_email='greenhoop777@gmail.com',
      url='',
      keywords='web',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      extras_require={
          'testing': tests_require,
      },
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = uwsgi_app:main
      """,
      # [console_scripts]
      # initialize_db = uwsgi.scripts.initializedb:main
      )
