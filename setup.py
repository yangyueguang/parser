from setuptools import setup, find_packages

setup(
    name='py-extractor',
    version='0.2.0',
    description='extract pdf',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
    ],
    author='super',
    url='https://github.com/yangyueguang/parser',
    author_email='2829969299@qq.com',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    keywords=["pdf", "extractor", "extracter", "parser"],
    long_description="extract pdf include edit or not",
    platforms="any",
    install_requires=['numpy', 'pandas', 'scikit-image', 'matplotlib', 'opencv-python', 'pillow', 'python-docx']
)