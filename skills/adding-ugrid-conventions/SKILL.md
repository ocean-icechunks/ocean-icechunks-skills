---
name: adding-ugrid-conventions
description: Add UGRID metadata to output from an unstructured-mesh ocean model (FVCOM, SHYFEM, SCHISM, ADCIRC, ICON, Delft3D FM) so xugrid, hvplot and other tools recognize the mesh, including when the data is a virtual Icechunk store. Use when a mesh-model dataset has node coordinates and a connectivity array but no `mesh_topology` variable, when xugrid fails to open or misreads a model file, or when asked to make mesh output CF/UGRID compliant. Covers the mesh topology variable, `cf_role`, `start_index` and `face_dimension` on connectivity (including FVCOM's transposed `nv`), node and face coordinates, `mesh` and `location` on data variables, and writing the topology variable into a virtual store after the data.
---

# Adding UGRID conventions to unstructured-mesh model output

**Experimental.** Checked against `xugrid` 0.15.3 on a small synthetic mesh and
against public builds and notebooks for FVCOM, SHYFEM, SCHISM, ADCIRC and ICON
(ICON is Provisional). See `references/check-with-xugrid.md`. Delft3D FM is named but
has not been exercised.

**Check first:** some output is already UGRID (newer SCHISM with `iof_ugrid`, NOAA
STOFS-2D ADCIRC). Try `xu.UgridDataset` on the file before adding anything.

Most mesh-model files hold the mesh (node coordinates, triangle connectivity)
but do not label it, so tools cannot recognize it. Adding UGRID means adding
attributes and, usually, one new scalar variable. The variable names differ by
model; the three gotchas below do not. Model-specific details are in the notes:

| Model | Notes | Main differences |
| --- | --- | --- |
| FVCOM | [references/fvcom.md](references/fvcom.md) | `nv` is `(three, nele)`, 1-based |
| SHYFEM | [references/shyfem.md](references/shyfem.md) | placeholder `topology` variable already exists |
| ADCIRC | [references/adcirc.md](references/adcirc.md) | STOFS-2D files are already UGRID; `fort.14` is text |
| SCHISM | [references/schism.md](references/schism.md) | native UGRID output, projected coordinates, quads, string mesh variable |
| ICON | [references/icon.md](references/icon.md) | separate grid file, coordinates in radians |

## What to add

1. **A mesh topology variable.** A scalar variable (name it `mesh_topology`, or
   reuse an existing placeholder such as SHYFEM's `topology`) with:

   ```python
   {
     "cf_role": "mesh_topology",
     "topology_dimension": 2,
     "node_coordinates": "lon lat",          # names of the node x and y variables
     "face_coordinates": "lonc latc",        # optional: face centres
     "face_node_connectivity": "nv",         # name of the connectivity array
     "face_dimension": "nele",               # see gotcha 1
   }
   ```

2. **The connectivity array** (`nv` in FVCOM, `element_index` in SHYFEM):
   `cf_role = "face_node_connectivity"` and `start_index` (gotcha 2).
3. **Node and face coordinate variables:** `standard_name` (`longitude` or
   `latitude`) and `units`.
4. **Each data variable on the mesh:** `mesh = "mesh_topology"` and
   `location = "node"` or `"face"`, chosen from the variable's dimension (a
   variable with the face dimension is on faces, with `node` on nodes).
5. **Global attribute:** `Conventions` including `UGRID-1.0`, appended to whatever
   the file already says (for example `"CF-1.11, UGRID-1.0"`).

## Three gotchas

1. **Dimension order of the connectivity array.** UGRID expects
   `(n_face, 3)`, with the face dimension first. FVCOM's `nv` is
   `(three, nele)`, the other way round. Do not transpose it (impossible in a
   virtual store without rewriting chunks); set `face_dimension` on the mesh
   topology variable to the face dimension's name. (For a dataset opened in memory,
   transposing the array also works.) Without it, `xugrid` raised an
   obscure NumPy error when the layout was transposed.
2. **`start_index`.** UGRID defaults to 0-based indexing. FVCOM, SHYFEM, SCHISM, ADCIRC
   and ICON connectivity is 1-based, so set `start_index = 1` on the connectivity
   variable. **Leaving it out does not fail.** In the check, `xugrid` opened the
   mesh and kept the 1-based ids, so a face referred to node id 5 on a 5-node
   mesh, which does not exist. Check the connectivity values after opening.
3. **Coordinates and static variables are different things.** Node and face
   longitude and latitude belong in `coords`. Connectivity (`nv`) and bathymetry
   (`h`) are data variables even though they never change; do not promote them to
   coordinates to protect them during a concat, because every downstream reader
   then sees them as coordinates.

## Virtual Icechunk stores

The source files usually have no mesh topology variable, and a new real variable
cannot be added to a virtual dataset before `to_icechunk`. Apply the variable
and global attributes (items 2 to 5) to the virtual dataset in memory, which
needs no data, and write the mesh topology variable into the store as an
ordinary Zarr array after the data, before committing:

```python
combined.vz.to_icechunk(session.store)
z = zarr.open_group(session.store, mode="r+")
arr = z.require_array("mesh_topology", shape=(), dtype="int32")
arr[()] = np.int32(0)
arr.attrs.update(MESH_TOPOLOGY_ATTRS)
session.commit("...")
```

Write it on every build with `require_array`, so re-runs do not fail. This is
the pattern in the public `necofs-provider` scripts (not re-run here).

## Verify

```python
import xugrid as xu
uds = xu.UgridDataset(xr.open_zarr(store, consolidated=False, chunks={}))
g = uds.grids[0]
g.n_node, g.n_face                      # match the file's dimensions
g.face_node_connectivity.min(), g.face_node_connectivity.max()   # 0 .. n_node - 1
```

Check that the counts match the file, that connectivity runs from 0 to
`n_node - 1`, and that a plot of one field looks like the model domain.
