from setuptools import setup, find_packages

setup(
    name='book_library_app',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask',
        'Flask-SQLAlchemy',
        'Flask-Login',
        'Werkzeug',
        'Flask-Migrate',
        'Pillow',
        'pyzbar',
        'requests',
    ],
)
