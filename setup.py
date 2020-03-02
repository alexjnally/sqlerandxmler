from setuptools import setup
import versioneer

requirements = [
    # package requirements go here
]

setup(
    name='sqlerandxmler',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Execute queries and parse XMLs",
    license="MIT",
    author="Alex Nally",
    author_email='alexjnally@gmail.com',
    url='https://github.com/alexjnally/sqlerandxmler',
    packages=['sqlerandxmler'],
    entry_points={
        'console_scripts': [
            'sqlerandxmler=sqlerandxmler.cli:cli'
        ]
    },
    install_requires=requirements,
    keywords='sqlerandxmler',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
