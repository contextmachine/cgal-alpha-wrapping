#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/Surface_mesh.h>
#include <CGAL/Polyhedron_3.h>
#include <CGAL/alpha_wrap_3.h>
#include <CGAL/Polygon_mesh_processing/polygon_soup_to_polygon_mesh.h>
#include <CGAL/Polygon_mesh_processing/triangulate_faces.h>
#include <vector>
#include <array>
#include <iostream>
template<typename T>
struct BufferAttribute {
    T* arr;
    size_t size;
};

struct TriMesh {
    BufferAttribute<double> vertices;
    BufferAttribute<size_t> indices;
};
    typedef CGAL::Exact_predicates_inexact_constructions_kernel K;
    typedef K::Point_3 Point_3;
    typedef CGAL::Surface_mesh<Point_3> Surface_mesh;
    typedef CGAL::Polyhedron_3<K> Polyhedron_3;

inline void alphaWrapTriMesh(TriMesh& mesh, double alpha, double offset) {


    // Step 1: Convert TriMesh to CGAL points
    std::vector<Point_3> points;
    size_t num_vertices = mesh.vertices.size / 3;
    points.reserve(num_vertices);

    for (size_t i = 0; i < num_vertices; ++i) {
        points.emplace_back(
            mesh.vertices.arr[i * 3],
            mesh.vertices.arr[i * 3 + 1],
            mesh.vertices.arr[i * 3 + 2]
        );
    }

    // Step 2: Create polygon soup from indices
    std::vector<std::array<size_t, 3>> triangles;
    size_t num_triangles = mesh.indices.size / 3;
    triangles.reserve(num_triangles);

    for (size_t i = 0; i < num_triangles; ++i) {
        triangles.push_back({
            mesh.indices.arr[i * 3],
            mesh.indices.arr[i * 3 + 1],
            mesh.indices.arr[i * 3 + 2]
        });
    }

    // Step 3: Apply alpha wrapping
    Surface_mesh wrap;
    CGAL::alpha_wrap_3(points, triangles, alpha, offset, wrap);

    // Step 4: Ensure all faces are triangulated
    //CGAL::Polygon_mesh_processing::triangulate_faces(wrap);

    // Step 5: Extract vertices from the wrapped mesh
    std::vector<double> new_vertices;
    std::vector<size_t> new_indices;

    // Create vertex index map
    std::map<Surface_mesh::Vertex_index, size_t> vertex_map;
    size_t vertex_idx = 0;

    for (auto v : wrap.vertices()) {
        const Point_3& p = wrap.point(v);
        new_vertices.push_back(p.x());
        new_vertices.push_back(p.y());
        new_vertices.push_back(p.z());
        vertex_map[v] = vertex_idx++;
    }

    // Extract triangulated faces
    for (auto f : wrap.faces()) {
        std::vector<size_t> face_vertices;
        for (auto v : vertices_around_face(wrap.halfedge(f), wrap)) {
            face_vertices.push_back(vertex_map[v]);
        }

        // Should be triangulated, so each face has exactly 3 vertices
        if (face_vertices.size() == 3) {
            new_indices.push_back(face_vertices[0]);
            new_indices.push_back(face_vertices[1]);
            new_indices.push_back(face_vertices[2]);
        }else{

          std::cerr<< "faces size: "<<face_vertices.size()<<std::endl;
           }
    }

    // Step 6: Allocate new memory and update the TriMesh structure
    // Clean up old data
    delete[] mesh.vertices.arr;
    delete[] mesh.indices.arr;

    // Allocate and copy new vertices
    mesh.vertices.size = new_vertices.size();
    mesh.vertices.arr = new double[mesh.vertices.size];
    std::copy(new_vertices.begin(), new_vertices.end(), mesh.vertices.arr);

    // Allocate and copy new indices
    mesh.indices.size = new_indices.size();
    mesh.indices.arr = new size_t[mesh.indices.size];
    std::copy(new_indices.begin(), new_indices.end(), mesh.indices.arr);
}