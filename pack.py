# coding: utf-8
import os, sys
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

SRC_DIR = "extractor"
MODULE_NAME = "extractor"
IGNORE_FILES = ["__init__.py"]


""" 扫描文件夹下所有的文件 """
def scandir(dir, files=[]):
    for file in os.listdir(dir):
        if file in IGNORE_FILES:
            continue
        path = os.path.join(dir, file)
        if os.path.isfile(path) and path.endswith(".py"):
            files.append(path.replace(os.path.sep, ".")[:-3])
        elif os.path.isdir(path):
            scandir(path, files)
    return files


def make_extension(extName):
    extPath = extName.replace(os.path.pardir, '**').replace(".", os.path.sep).replace('**', os.path.pardir) + ".py"
    return Extension(extName, [extPath], include_dirs=["."])


def get_packages(folder, packages=[]):
    for file in os.listdir(folder):
        if file in IGNORE_FILES:
            continue
        path = os.path.join(folder, file)
        if os.path.isdir(path) and os.path.exists('{}/__init__.py'.format(path)):
            packages.append(path)
            get_packages(path, packages)
    packages.append(folder)
    return [p.replace('/', '.') for p in packages]


def clean(target_dir):
    for file in os.listdir(target_dir):
        path = os.path.join(target_dir, file)
        if os.path.isfile(path) and file not in IGNORE_FILES:
            if file.endswith('c') or file.endswith('so'):
                os.system("rm -f {}".format(path))
        elif os.path.isdir(path):
            clean(path)


def copy_so(target_dir, build_base_dir, taget_base_dir):
    for file in os.listdir(target_dir):
        path = os.path.join(target_dir, file)
        if os.path.isfile(path) and path.endswith(".so"):
            new_path = path.replace(build_base_dir, taget_base_dir)
            os.system("cp {} {}".format(path, new_path))
        elif os.path.isdir(path):
            copy_so(path, build_base_dir, taget_base_dir)


if __name__ == '__main__':
    ext_names = scandir(SRC_DIR)
    extensions = [make_extension(name) for name in ext_names]
    packages = get_packages(SRC_DIR)
    setup(
        name=MODULE_NAME,
        packages=packages,
        ext_modules=extensions,
        cmdclass={'build_ext': build_ext},
        requires=['numpy', 'pandas', 'scikit_image', 'matplotlib', 'opencv_python', 'pillow', 'python_docx']
    )
    temp_dir, lib_dir = os.listdir('build')
    build_base_dir = os.path.join('build', lib_dir, SRC_DIR)
    copy_so(build_base_dir, build_base_dir, SRC_DIR)
    clean(SRC_DIR)
    os.system('mv build/%s/%s build/' % (lib_dir, SRC_DIR))
    os.system('rm -rf build/%s build/%s' % (temp_dir, lib_dir))
