# Check: what `xugrid` does with and without each attribute

A tiny FVCOM-style mesh: 5 nodes, 3 triangles, connectivity `nv` shaped
`(three, nele)` with 1-based node ids, and a scalar `mesh_topology`. Run with
`xugrid` 0.15.3, `xarray` and `numpy`.

```python
import numpy as np, xarray as xr, xugrid as xu

def make(face_dimension=True, start_index=True, transposed=True):
    lon = np.array([0., 1., 2., 0., 1.]); lat = np.array([0., 0., 0., 1., 1.])
    tri = np.array([[1, 2, 5], [1, 5, 4], [2, 3, 5]])      # 3 faces, 1-based node ids
    nv = tri.T if transposed else tri                      # FVCOM: (three, nele)
    dims = ("three", "nele") if transposed else ("nele", "three")
    ds = xr.Dataset({
        "lon": ("node", lon, {"standard_name": "longitude", "units": "degrees_east"}),
        "lat": ("node", lat, {"standard_name": "latitude", "units": "degrees_north"}),
        "nv": (dims, nv, {"cf_role": "face_node_connectivity",
                          **({"start_index": 1} if start_index else {})}),
        "zeta": (("time", "node"), np.arange(10.).reshape(2, 5)),
        "mesh_topology": ((), np.int32(0), {
            "cf_role": "mesh_topology", "topology_dimension": 2,
            "node_coordinates": "lon lat", "face_node_connectivity": "nv",
            **({"face_dimension": "nele"} if face_dimension else {})}),
    })
    ds["zeta"].attrs.update(mesh="mesh_topology", location="node")
    return ds

g = xu.UgridDataset(make()).grids[0]
print(g.n_node, g.n_face, g.face_node_connectivity.tolist())
```

## Results

| Case | Result |
|---|---|
| `(three, nele)`, `face_dimension`, `start_index = 1` | 5 nodes, 3 faces, connectivity `[[0,1,4],[0,4,3],[1,2,4]]`: correct, now 0-based |
| `(three, nele)`, **no** `face_dimension` | `ValueError` from NumPy boolean indexing: obscure, fails loudly |
| `(three, nele)`, `face_dimension`, **no** `start_index` | Opens without error; connectivity `[[1,2,5],[1,5,4],[2,3,5]]`: still 1-based, and node id 5 does not exist on a 5-node mesh. **Silent.** |
| `(nele, three)`, no `face_dimension` | Correct: the default layout needs no `face_dimension` |

The silent case is the one to guard against. Always compare the connectivity
range with the node count after opening.

## Not checked here

- Behavior of other readers (for example the `UGRID` support in other tools).
- Edge-based meshes or `topology_dimension` of 1 or 3.
- Mixed triangle/quad meshes with `_FillValue` in the connectivity array.

## Public examples

- An FVCOM wave forecast store with all the attributes above and the
  after-the-data `mesh_topology` write: the scripts in
  `OpenScienceComputing/necofs-provider` (`CF_VAR_ATTRS`,
  `MESH_TOPOLOGY_ATTRS`, `add_ugrid_metadata`, `write_mesh_topology`).
- SHYFEM (a placeholder `topology` variable plus `element_index`):
  `cf_ugrid_tutorial.ipynb`, section 2.3, in `rsignell/MAGICA-School-2026`.
