import os
from setuptools import setup, find_packages

# Read README.md safely
this_directory = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(this_directory, "README.md")

if os.path.exists(readme_path):
    with open(readme_path, encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "A versatile timing decorator"

setup(
    name='timeit_decorator',
    version='2.0.0',
    author='jubnl',
    license='MIT',
    author_email='jgunther021@gmail.com',
    packages=[
        "timeit_decorator"
    ],
    install_requires=[
        "tabulate>=0.9.0"
    ],
    description='A versatile timing decorator',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/jubnl/timeit_decorator',
    python_requires='>=3.7',  # Ensures compatibility
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': [
            'timeit_decorator=timeit_decorator.__main__:main',
        ],
    },
)