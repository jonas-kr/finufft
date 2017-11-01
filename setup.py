from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import setuptools

__version__ = '0.1.1g'

# Publish the library to PyPI (from DFM):
if "publish" in sys.argv[-1]:
    os.system("python setup.py sdist upload")
    sys.exit()

class get_pybind_include(object):
    """Helper class to determine the pybind11 include path

    The purpose of this class is to postpone importing pybind11
    until it is actually installed, so that the ``get_include()``
    method can be invoked. """

    def __init__(self, user=False):
        self.user = user

    def __str__(self):
        import pybind11
        return pybind11.get_include(self.user)

libraries = ["lib-static/finufft","fftw3","fftw3_threads"]
extra_compile_args=['-fopenmp'],
extra_link_args=['-lgomp']

ext_modules = [Extension(
        'finufftpy_cpp',
        ['finufftpy/finufftpy.cpp'],
        include_dirs=[
            # Path to pybind11 headers
            get_pybind_include(),
            get_pybind_include(user=True),
            'src'
        ],
        libraries=libraries,
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        language='c++'
    ) ]

# As of Python 3.6, CCompiler has a `has_flag` method.
# cf http://bugs.python.org/issue26689
def has_flag(compiler, flagname):
    """Return a boolean indicating whether a flag name is supported on
    the specified compiler.
    """
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.cpp') as f:
        f.write('int main (int argc, char **argv) { return 0; }')
        try:
            compiler.compile([f.name], extra_postargs=[flagname])
        except setuptools.distutils.errors.CompileError:
            return False
    return True


def cpp_flag(compiler):
    """Return the -std=c++[11/14] compiler flag.

    The c++14 is prefered over c++11 (when it is available).
    """
    if has_flag(compiler, '-std=c++14'):
        return '-std=c++14'
    elif has_flag(compiler, '-std=c++11'):
        return '-std=c++11'
    else:
        raise RuntimeError('Unsupported compiler -- at least C++11 support '
                           'is needed!')


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""
    c_opts = {
        'msvc': ['/EHsc'],
        'unix': [],
    }

    if sys.platform == 'darwin':
        c_opts['unix'] += ['-stdlib=libc++', '-mmacosx-version-min=10.7']

    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        if ct == 'unix':
            opts.append('-DVERSION_INFO="%s"' % self.distribution.get_version())
            opts.append(cpp_flag(self.compiler))   # AHB: C++11 not used now, but David Stein says needed.
            if has_flag(self.compiler, '-fvisibility=hidden'):
                opts.append('-fvisibility=hidden')
        elif ct == 'msvc':
            opts.append('/DVERSION_INFO=\\"%s\\"' % self.distribution.get_version())
        for ext in self.extensions:
            ext.extra_compile_args = opts
        build_ext.build_extensions(self)


########## SETUP ###########
setup(
    name='finufftpy',
    version=__version__,
    author='python interfaces by: Daniel Foreman-Mackey, Jeremy Magland, and Alex Barnett',
    author_email='abarnett@flatironinstitute.org',
    url='http://github.com/ahbarnett/finufft',
    description='python interface to FINUFFT',
    long_description='python interface to FINUFFT (Flatiron Institute Nonuniform Fast Fourier Transform) library.',
    license="Apache 2",
    ext_modules=ext_modules,
    packages=['finufftpy'],
    install_requires=['numpy','pybind11>=2.2'],
    cmdclass={'build_ext': BuildExt},
    zip_safe=False,
)

