# FVCOM

Status: used on NECOFS (virtual Icechunk) and the UMass Dartmouth GOM3 hindcast (in-memory).

## What the files have

| Role | Name | Notes |
| --- | --- | --- |
| Node coordinates | `lon`, `lat` | dimension `node` |
| Face-centre coordinates | `lonc`, `latc` | dimension `nele` |
| Connectivity | `nv` | `(three, nele)`, **1-based**: the transpose of what UGRID expects |
| Vertical | `siglay`, `siglev` | 2-D coordinates `(siglay, node)`; not mesh coordinates |

A variable with dimension `nele` is on faces; with `node` it is on nodes.

## Mesh topology attributes

```python
MESH_TOPOLOGY_ATTRS = {
    "cf_role": "mesh_topology",
    "topology_dimension": 2,
    "node_coordinates": "lon lat",
    "face_coordinates": "lonc latc",
    "face_node_connectivity": "nv",
    "face_dimension": "nele",
}
```

On `nv`: `cf_role = "face_node_connectivity"`, `start_index = 1`.

## Orientation of `nv`: two routes

- **Virtual store:** leave `nv` as `(three, nele)` and rely on `face_dimension = "nele"`.
  A virtual store cannot be transposed without rewriting chunks. This is the route the
  NECOFS build uses.
- **Dataset opened in memory** (zarr or NetCDF): `ds["nv"] = ds["nv"].transpose("nele", "three")`
  is also fine, and the GOM3 example does that and sets `face_dimension`. Pick one per
  workflow and verify with xugrid (see `SKILL.md`).

## Examples

- NECOFS wave store, attributes plus the post-write `mesh_topology`:
  [necofs-provider](https://github.com/OpenScienceComputing/necofs-provider),
  `process_wave_timeseries.py`.
- GOM3 hindcast, in-memory `add_ugrid_metadata`:
  [gist](https://gist.github.com/rsignell/2ee54d379b15be4b8a101c5dec68bd6d).
