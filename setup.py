from setuptools import setup, find_packages

setup(
    name='timeit_decorator',
    version='1.0.2',
    author='jubnl',
    author_email='jgunther021@gmail.com',
    packages=find_packages(),
    install_requires=[],
    description='A versatile timing decorator',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/jubnl/timeit_decorator',
    classifiers=[
        # Classifiers help users find your project
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)