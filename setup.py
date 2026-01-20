from setuptools import setup, Extension

module = Extension('x11_keyboard',
                   sources=['x11_keyboard.cpp'],
                   libraries=['X11', 'Xtst'],
                   extra_compile_args=['-std=c++11'])

setup(name='x11_keyboard',
      version='1.0',
      description='X11 keyboard simulator using XTest',
      ext_modules=[module])