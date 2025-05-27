# distutils: language = c++
# cython: language_level=3
cimport cython
import numpy as np
cimport numpy as np
from libcpp cimport bool
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy

# Ensure numpy is initialized
np.import_array()

# C++ structure declarations
cdef extern from "cgal_alpha_wrapping_cpp.h":
    

    cdef cppclass BufferAttribute[T]:
        T* arr
        size_t size

    ctypedef struct TriMesh:
        BufferAttribute[double] vertices
        BufferAttribute[size_t] indices

    void alphaWrapTriMesh(TriMesh& mesh, double alpha, double offset) except +

@cython.cdivision(True)
@cython.initializedcheck(False)
@cython.boundscheck(False)
@cython.wraparound(False)
def alpha_wrap(double[:, :] vertices, long[:, :] faces, double alpha=0.1, double offset=0.1):
    """
    Apply CGAL alpha wrapping to a triangulated mesh.

    Parameters
    ----------
    vertices : numpy.ndarray, shape (n_vertices, 3), dtype=float64
        Vertex coordinates
    faces : numpy.ndarray, shape (n_faces, 3), dtype=int32 or int64
        Triangle face indices
    alpha : float, optional
        Alpha value controlling the size of alpha balls (default: 0.1)
    offset : float, optional
        Uniform offset added to the wrapping surface (default: 0.0)
  

    Returns
    -------
    wrapped_vertices : numpy.ndarray, shape (n_wrapped_vertices, 3), dtype=float64
        Vertices of the wrapped mesh
    wrapped_faces : numpy.ndarray, shape (n_wrapped_faces, 3), dtype=int64
        Triangle face indices of the wrapped mesh
    """
    cdef:
        TriMesh mesh
        size_t n_vertices = vertices.shape[0]
        size_t n_faces = faces.shape[0]
        size_t i, j
        double* vert_ptr
        size_t* idx_ptr

    # Validate input
    if vertices.shape[1] != 3:
        raise ValueError("Vertices must have shape (n, 3)")
    if faces.shape[1] != 3:
        raise ValueError("Faces must have shape (n, 3)")

    # Allocate and copy vertex data
    mesh.vertices.size = n_vertices * 3
    mesh.vertices.arr = <double*>malloc(mesh.vertices.size * sizeof(double))
    if not mesh.vertices.arr:
        raise MemoryError("Failed to allocate memory for vertices")

    # Copy vertices (flatten from n×3 to n*3)
    vert_ptr = mesh.vertices.arr
    for i in range(n_vertices):
        for j in range(3):
            vert_ptr[i * 3 + j] = vertices[i, j]

    # Allocate and copy face data
    mesh.indices.size = n_faces * 3
    mesh.indices.arr = <size_t*>malloc(mesh.indices.size * sizeof(size_t))
    if not mesh.indices.arr:
        free(mesh.vertices.arr)
        raise MemoryError("Failed to allocate memory for indices")

    # Copy faces (flatten from n×3 to n*3)
    idx_ptr = mesh.indices.arr
    for i in range(n_faces):
        for j in range(3):
            idx_ptr[i * 3 + j] = <size_t>faces[i, j]

    # Call the C++ function
    try:
        alphaWrapTriMesh(mesh, alpha, offset)
    except Exception as e:
        # Clean up on error
        free(mesh.vertices.arr)
        free(mesh.indices.arr)
        raise RuntimeError(f"Alpha wrapping failed: {str(e)}")

    # Convert results back to numpy arrays
    cdef:
        size_t new_n_vertices = mesh.vertices.size // 3
        size_t new_n_faces = mesh.indices.size // 3
        np.ndarray[double, ndim=2] wrapped_vertices = np.empty((new_n_vertices, 3), dtype=np.float64)
        np.ndarray[np.int64_t, ndim=2] wrapped_faces = np.empty((new_n_faces, 3), dtype=np.int64)

    # Copy wrapped vertices
    vert_ptr = mesh.vertices.arr
    for i in range(new_n_vertices):
        for j in range(3):
            wrapped_vertices[i, j] = vert_ptr[i * 3 + j]

    # Copy wrapped faces
    idx_ptr = mesh.indices.arr
    for i in range(new_n_faces):
        for j in range(3):
            wrapped_faces[i, j] = idx_ptr[i * 3 + j]

    # Clean up allocated memory
    free(mesh.vertices.arr)
    free(mesh.indices.arr)

    return wrapped_vertices, wrapped_faces

