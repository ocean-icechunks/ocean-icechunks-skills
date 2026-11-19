---
name: adding-ugrid-conventions
description: Use when a dataset from an unstructured-mesh ocean model (FVCOM, SHYFEM, SCHISM, ADCIRC, Delft3D FM) lacks UGRID metadata, or when preparing such data (including virtual Icechunk stores) so xugrid, hvplot and other tools recognize the mesh. Covers the mesh_topology variable, the cf_role, start_index and face_dimension attributes on connectivity (including FVCOM's transposed nv), node and face coordinates, the mesh and location attributes on data variables, and adding the mesh_topology variable to a virtual store after writing.
---

# Adding UGRID conventions to unstructured-mesh model output

**Status: Experimental.** The guidance comes from FVCOM and SHYFEM output; SCHISM,
ADCIRC and Delft3D FM are named in the description but have not been exercised.

Most model files hold the mesh (node coordinates, triangle connectivity) but
do not label it, so tools cannot recognize it. Adding UGRID means adding
attributes and, usually, one new scalar variable. It needs no model-specific
skill; the model-specific parts are the variable names and the three gotchas
below.

## The attributes

1. **A mesh topology variable.** A scalar variable (name it `mesh_topology`
   or reuse an existing placeholder like SHYFEM's `topology`) with:

   ```python
   {
     "cf_role": "mesh_topology",
     "topology_dimension": 2,
     "node_coordinates": "lon lat",          # names of the node x/y variables
     "face_coordinates": "lonc latc",        # optional: face centres
     "face_node_connectivity": "nv",         # name of the connectivity array
     "face_dimension": "nele",               # see gotcha 1
   }
   ```

2. **The connectivity array** (`nv` in FVCOM, `element_index` in SHYFEM):
   `cf_role = "face_node_connectivity"` and `start_index` (gotcha 2).
3. **Node and face coordinate variables**: `standard_name` of `longitude` or
   `latitude` and `units` (and `axis` where it applies).
4. **Each data variable on the mesh**: `mesh = "mesh_topology"` and
   `location = "node"` or `"face"`. Choose `location` from the variable's
   dimension (a variable with the `nele` dimension is on faces, with `node` on
   nodes).
5. **Global attribute**: `Conventions = "CF-1.11, UGRID-1.0"` (append UGRID to
   whatever the file already says).

## Three gotchas

1. **Dimension order of the connectivity array.** UGRID expects
   `(n_face, 3)`, with the face dimension first. FVCOM's `nv` is
   `(three, nele)`, the other way round. Do not transpose (impossible in a
   virtual store without rewriting chunks); set `face_dimension` on the mesh
   topology variable to the name of the face dimension (`"nele"`) so readers
   know which axis is which. Without it, the array is read transposed or fails.
2. **`start_index`.** UGRID defaults to 0-based indexing. FVCOM and SHYFEM
   connectivity is 1-based, so set `start_index = 1` on the connectivity
   variable. Omitting it shifts every triangle by one node.
3. **Static variables are not coordinates.** `nv`, bathymetry (`h`) and other
   static arrays stay data variables, whatever concat treatment they need.
   Real coordinates (node and face lon/lat) go in `coords`. See the
   `virtual-icechunk` skill for which is which and for how
   to protect static variables during concat.

## Adding the mesh topology variable to a virtual Icechunk store

The source files usually have no such variable, and you cannot add a new
real variable to a virtual dataset before `to_icechunk`. Write it into the
store afterwards as an ordinary Zarr array, before committing:

```python
combined.vz.to_icechunk(session.store)
z = zarr.open_group(session.store, mode="r+")
arr = z.require_array("mesh_topology", shape=(), dtype="int32")
arr[()] = np.int32(0)
arr.attrs.update(MESH_TOPOLOGY_ATTRS)
session.commit("...")
```

Apply the variable-level and global attributes (items 2 to 5) to the virtual
dataset in memory before writing; they are small and are stored in the Zarr
metadata. Write the mesh variable on every build, with `require_array`, so
re-runs do not fail.

## Verify

```python
import xugrid as xu
uds = xu.UgridDataset(xr.open_zarr(session.store, consolidated=False, chunks={}))
uds.ugrid.grids          # one 2-D mesh with the expected n_node and n_face
uds["<variable>"].isel(time=0).ugrid.plot()
```

Check that the face and node counts match the file's dimensions and that a
plot of one field looks like the model domain. A transposed or off-by-one
connectivity gives obviously scrambled triangles.

## Source examples

- FVCOM wave store, all attributes and the post-write `mesh_topology`:
  [OpenScienceComputing/necofs-provider](https://github.com/OpenScienceComputing/necofs-provider),
  `process_wave_timeseries.py` (`CF_VAR_ATTRS`, `MESH_TOPOLOGY_ATTRS`,
  `add_ugrid_metadata`, `write_mesh_topology`).
- SHYFEM (a placeholder `topology` variable plus `element_index`):
  [OpenScienceComputing/MAGICA-School-2026](https://github.com/OpenScienceComputing/MAGICA-School-2026),
  `cf_ugrid_tutorial.ipynb`, section 2.3.
