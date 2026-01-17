from setuptools import setup, Extension

module = Extension('uinput_keyboard',
                   sources=['uinput_keyboard.cpp'],
                   extra_compile_args=['-std=c++11'])

setup(name='uinput_keyboard',
      version='1.0',
      description='Linux uinput keyboard simulator',
      ext_modules=[module])