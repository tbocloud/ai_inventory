from setuptools import setup, find_packages

# Read requirements from requirements.txt
with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='ai_inventory',
    version='2.1.0',
    description='AI-powered inventory and sales forecasting for ERPNext',
    author='AI Inventory Team',
    author_email='support@ai-inventory-forecast.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=requirements,
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
