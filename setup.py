import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='typeytypey',
    version='0.1.0',
    author='Michael Davies',
    author_email='michael@the-davies.net',
    description='A Linux CLI demo replay tool, written in Python 3',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mrda/typeytypey',
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
        'typeytypey = typeytypey.typeytypey:main'
        ],
    },
)

