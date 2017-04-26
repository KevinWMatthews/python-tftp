from setuptools import setup

setup(name='tftp',
    version='0.1',
    description='Test-drive Python TFTP library',
    author='Kevin W Matthews',
    author_email='KevinWMatthews@gmail.com',
    license='MIT',
    packages=['tftp'],
    zip_safe=False,
    scripts=['bin/tftp_get', 'bin/generate_random_string'],
)
