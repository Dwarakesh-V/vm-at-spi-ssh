from setuptools import setup, Extension

keyboard_module = Extension(
    'x11_keyboard',
    sources=['x11_keyboard.cpp'],
    libraries=['X11', 'Xtst'],
    extra_compile_args=['-std=c++11']
)

mouse_module = Extension(
    'x11_mouse',
    sources=['x11_mouse.cpp'],
    libraries=['X11', 'Xtst'],
    extra_compile_args=['-std=c++11']
)

setup(
    name='x11_input',
    version='1.0',
    description='X11 keyboard and mouse simulator using XTest',
    ext_modules=[keyboard_module, mouse_module]
)
