# ICON

Status: Provisional. Used on ICON-ESM-ER ocean output (EERIE, R02B09 grid, 14.9 million cells)
opened from a kerchunk/Zarr reference, so in memory, not as a virtual Icechunk store.
Source: [ICON_xugrid gist](https://gist.github.com/rsignell/6bd00aa9f8067d75e9d8c210797fad5f).

## What differs from the unstructured coastal models

- **The mesh is a separate grid file.** The data files hold fields only; the grid (a Zarr
  here) holds `vertex_of_cell`, `vlon`/`vlat`, `clon`/`clat`, and so on. Merge it into the data
  with `xr.merge`. Data and grid name the same dimensions differently (`ncells`, `ncells_2` in
  the data; cell and edge in the grid): rename the data dimensions to match the grid first.
  One coordinate (`cell_sea_land_mask`) had to be dropped for the merge to work; the reason was
  not found.
- **Coordinates are in radians.** `clon`, `clat`, `vlon`, `vlat` (and edge equivalents) are in
  radians. Convert with `np.rad2deg` (keeping attrs) and set `units` to `degrees_east` /
  `degrees_north` and `standard_name` to `longitude` / `latitude`. In a virtual store that means
  writing new real arrays, not editing references.
- **Connectivity is `vertex_of_cell` `(nv=3, cell)`, 1-based.** The gist transposes it to
  `(cell, 3)` in memory and sets `start_index = 1` and `_FillValue = -1`. Using `face_dimension`
  instead (as for FVCOM) was not tried on ICON.

## Mesh topology attributes

```python
{"cf_role": "mesh_topology", "topology_dimension": 2,
 "node_coordinates": "vlon vlat", "face_coordinates": "clon clat",
 "face_node_connectivity": "vertex_of_cell"}
```

Put `vlon vlat`, `clon clat` in coordinates (`set_coords`).

## Pitfall in the gist as written

The function that adds `mesh` / `location` to data variables tests for the dimensions
`ncells` and `nvertices`, but by then the dimensions have been renamed to `cell` and `vertex`,
so those attributes are not applied. Use the dataset's actual dimension names after any
renaming. xugrid still built the mesh from the topology variable, so the omission did not stop
the example from plotting.

## Cost

`xu.UgridDataset` on the 14.9-million-cell grid took about 40 seconds to 5 minutes. Subset with
`uds.ugrid.sel(x=slice(...), y=slice(...))` before plotting; the gist does that for the
Mediterranean.

## Examples

- [ICON_xugrid gist](https://gist.github.com/rsignell/6bd00aa9f8067d75e9d8c210797fad5f)
  (also the earlier `icon_ugrid` notebooks).
