from setuptools import setup, find_packages

setup(
    name='restaurant-service',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask==3.0.2',
        'flask-sqlalchemy==3.1.1',
        'flask-jwt-extended==4.6.0',
        'flask-migrate==4.0.5',
        'psycopg2-binary==2.9.9',
        'python-dotenv==1.0.1',
        'gunicorn==21.2.0',
    ],
    extras_require={
        'test': [
            'pytest==8.0.2',
            'pytest-cov==4.1.0',
        ],
    },
) 