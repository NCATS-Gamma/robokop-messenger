"""Setup file for messenger package."""
from setuptools import setup

setup(
    name='messenger',
    version='0.1.0-dev',
    author='Patrick Wang',
    author_email='patrick@covar.com',
    url='https://github.com/NCATS-Gamma/robokop-messenger',
    description='ROBOKOP Message-passing modules',
    packages=['messenger'],
    package_data={'messenger': ['reasoner.yaml']},
    include_package_data=True,
    zip_safe=False,
    license='MIT',
    python_requires='>=3.6',
)
