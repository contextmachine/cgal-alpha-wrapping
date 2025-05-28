from setuptools import setup, Extension, Distribution
from Cython.Build import cythonize
import numpy as np
import platform
import os
import sys
import setuptools

# Detect platform
system = platform.system()
machine = platform.machine()

# Base configuration
include_dirs = [np.get_include()]
library_dirs = []
libraries = ['gmp', 'mpfr']
extra_compile_args = ['-O3']
extra_link_args = []

if system == 'Linux':
    include_dirs.extend([
        '/usr/include',
        '/usr/include/eigen3',
        '/usr/local/include',
        '/usr/local/include/eigen3'
    ])
    library_dirs.extend([
        '/usr/lib',
        '/usr/lib/x86_64-linux-gnu',
        '/usr/local/lib'
    ])
    extra_compile_args.extend(['-std=c++17', '-frounding-math'])
    extra_link_args.append('-std=c++17')

elif system == 'Darwin':  # macOS
    if machine == 'arm64':
        homebrew_prefix = '/opt/homebrew'
    else:
        homebrew_prefix = '/usr/local'
    include_dirs.extend([
        f'{homebrew_prefix}/include',
        f'{homebrew_prefix}/include/eigen3',
        '/usr/local/include',
        '/usr/local/include/eigen3'
    ])
    library_dirs.extend([
        f'{homebrew_prefix}/lib',
        '/usr/local/lib'
    ])
    extra_compile_args.extend(['-std=c++17', '-stdlib=libc++', '-mcpu=apple-m1', '-flto'])
    extra_link_args.extend(['-std=c++17', '-stdlib=libc++', '-flto'])

elif system == 'Windows':
    vcpkg_root = os.environ.get('VCPKG_ROOT', 'C:/vcpkg')
    cgal_root = os.environ.get('CGAL_DIR', 'C:/CGAL')
    include_dirs.extend([
        f'{vcpkg_root}/installed/x64-windows/include',
        f'{cgal_root}/include',
        f'{cgal_root}/auxiliary/gmp/include',
        'C:/boost/include',
        'C:/Program Files/CGAL/include',
        'C:/local/include'
    ])
    library_dirs.extend([
        f'{vcpkg_root}/installed/x64-windows/lib',
        f'{cgal_root}/lib',
        f'{cgal_root}/auxiliary/gmp/lib',
        'C:/boost/lib',
        'C:/Program Files/CGAL/lib',
        'C:/local/lib'
    ])
    # Use the unversioned library names provided by vcpkg
    libraries = ['gmp', 'mpfr']
    extra_compile_args = ['/OX', '/std:c++17', '/EHsc']
    extra_link_args = []
    extra_compile_args.extend([
        '/D_USE_MATH_DEFINES',
        '/DNOMINMAX',
        '/DCGAL_DISABLE_ROUNDING_MATH_CHECK'
    ])

# Allow environment overrides
for var, lst in [('CGAL_INCLUDE_DIR', include_dirs), ('CGAL_LIBRARY_DIR', library_dirs), ('EIGEN3_INCLUDE_DIR', include_dirs)]:
    if var in os.environ:
        lst.insert(0, os.environ[var])

# Filter out non-existent directories
include_dirs = [d for d in include_dirs if os.path.exists(d)]
library_dirs = [d for d in library_dirs if os.path.exists(d)]

# Debug output
logo = rf"""
{platform.uname()}
compile_args: {extra_compile_args}
"""
print(logo)
print(f"Platform: {system} {machine}")
print(f"Include directories: {include_dirs}")
print(f"Library directories: {library_dirs}")
print(f"Libraries: {libraries}")

extensions = [
    Extension(
        "cgal_alpha_wrapping._cgal_alpha_wrapping",
        ["cgal_alpha_wrapping/_cgal_alpha_wrapping.pyx"],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        libraries=libraries,
        language="c++",
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
    )
]

compiler_directives = dict(
    boundscheck=False,
    wraparound=False,
    cdivision=True,
    nonecheck=False,
    overflowcheck=False,
    initializedcheck=False,
    embedsignature=True,
    language_level="3str",
)

def get_version():
    return os.environ.get('CGAL_ALPHA_WRAPPING_VERSION', '0.1.0')

if __name__ == "__main__":
    print(logo)
    ext_modules = cythonize(
        extensions,
        nthreads=os.cpu_count(),
        include_path=[np.get_include()],
        compiler_directives=compiler_directives
    )
    version = get_version()
    dist = Distribution({
        "ext_modules": ext_modules,
        "name": "cgal-alpha-wrapping",
        "version": version
    })
    cmd = build_ext(dist)
    cmd.ensure_finalized()
    cmd.run()

    import shutil
    for output in cmd.get_outputs():
        rel = os.path.relpath(output, cmd.build_lib)
        shutil.copyfile(output, rel)
