# SHYFEM

Status: used on SHYFEM output for Antsiranana Bay, Madagascar (in-memory, CF-1.4-style files).

## What the files have

The mesh is present but unlabelled: a placeholder scalar variable `topology`, the
connectivity array `element_index`, and node coordinates `longitude` / `latitude`.
Vertical dimension `level`.

## What to add

```python
ds["topology"].attrs.update({
    "cf_role": "mesh_topology",
    "topology_dimension": 2,
    "node_coordinates": "longitude latitude",
    "face_node_connectivity": "element_index",
})
ds["element_index"].attrs.update({"cf_role": "face_node_connectivity", "start_index": 1})
ds["longitude"].attrs["standard_name"] = "longitude"
ds["latitude"].attrs["standard_name"] = "latitude"
ds = ds.set_coords(["longitude", "latitude"])   # keep `topology` in data_vars
```

Reuse the existing `topology` variable instead of adding a second mesh variable.
`start_index = 1` because SHYFEM node indices are 1-based.

`face_dimension` was not needed in the tutorial, which means `element_index` was already
face-first; check the orientation in your own file before relying on that.

After this, `xu.UgridDataset(ds)` detects the mesh without further help.

## Examples

- Tutorial, section 2.3:
  [MAGICA-School-2026](https://github.com/OpenScienceComputing/MAGICA-School-2026),
  `cf_ugrid_tutorial.ipynb`.
- Analysis notebook: [gist](https://gist.github.com/rsignell/c468ecdd033cea920761bcc3d9b4d565).
