---
name: adding-ugrid-conventions
description: Use when a dataset from an unstructured-mesh ocean model (FVCOM, SHYFEM, SCHISM, ADCIRC, ICON, Delft3D FM) lacks UGRID metadata, or when preparing such data (including virtual Icechunk stores) so xugrid, hvplot and other tools recognize the mesh. Covers the mesh_topology variable, the cf_role, start_index and face_dimension attributes on connectivity (including FVCOM's transposed nv), node and face coordinates, the mesh and location attributes on data variables, and adding the mesh_topology variable to a virtual store after writing.
---

# Adding UGRID conventions to unstructured-mesh model output

**Status: Experimental.** The guidance comes from FVCOM, SHYFEM, SCHISM, ADCIRC and ICON
output. Delft3D FM is named in the description but has not been exercised.

**Check first:** some output is already UGRID (newer SCHISM with `iof_ugrid`, NOAA STOFS-2D
ADCIRC). Try `xu.UgridDataset` on the file before adding anything.

Most model files hold the mesh (node coordinates, triangle connectivity) but
do not label it, so tools cannot recognize it. Adding UGRID means adding
attributes and, usually, one new scalar variable. The general pattern is
below; the model-specific parts (variable names, units, quirks) are in the per-model
notes.

| Model | Notes | Main differences |
| --- | --- | --- |
| FVCOM | [references/fvcom.md](references/fvcom.md) | `nv` is `(three, nele)`, 1-based |
| SHYFEM | [references/shyfem.md](references/shyfem.md) | placeholder `topology` variable already exists |
| ADCIRC | [references/adcirc.md](references/adcirc.md) | STOFS-2D files are already UGRID; `fort.14` is text |
| SCHISM | [references/schism.md](references/schism.md) | native UGRID output, projected coordinates, quads, string mesh variable |
| ICON | [references/icon.md](references/icon.md) | separate grid file, coordinates in radians |

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
   `(three, nele)`, the other way round. In a virtual store you cannot transpose
   (it would mean rewriting chunks), so set `face_dimension` on the mesh
   topology variable to the name of the face dimension (`"nele"`) so readers
   know which axis is which. Without it, the array is read transposed or fails.
   For a dataset opened in memory, transposing the array also works.
2. **`start_index`.** UGRID defaults to 0-based indexing. FVCOM, SHYFEM, SCHISM, ADCIRC
   and ICON connectivity is 1-based, so set `start_index = 1` on the connectivity
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

Each per-model note links its examples (public repositories and gists). The FVCOM and
SHYFEM ones are
[necofs-provider](https://github.com/OpenScienceComputing/necofs-provider) and
[MAGICA-School-2026](https://github.com/OpenScienceComputing/MAGICA-School-2026).
