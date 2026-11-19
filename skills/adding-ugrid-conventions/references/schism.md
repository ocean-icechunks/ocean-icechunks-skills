# SCHISM

Status: used on a SCHISM run (Test_CORIE) built as a virtual Icechunk store, private and
public copies. Source: [schism-skypilot-corie](https://github.com/ESIPFed/schism-skypilot-corie).

## Check first: newer SCHISM writes UGRID itself

With scribed I/O (`OLDIO=OFF`), the `param.nml` flag `iof_ugrid` controls this: `0` = no UGRID
metadata, `1` = full mesh data embedded in every 3D file, `2` = 3D files reference the mesh
written once in `out2d_*.nc`. With it on, `out2d_*.nc` has a `cf_role = "mesh_topology"`
variable, face and edge connectivity and a CF-1.12 `Conventions`. Inspect the actual file
rather than trusting the flag. Output from older configurations will need the usual attributes.

## Gotchas found on real output

1. **Concatenating files.** `xr.concat` with the default `data_vars="all"` stacks static
   connectivity arrays along the concat dimension, giving them a spurious extra dimension that
   xugrid rejects. Use `data_vars="minimal"` (also `coords="minimal"`, `compat="override"`).
2. **Projected coordinates.** With `ics = 1` SCHISM writes projected coordinates (State Plane
   metres in the example), but viewers need degrees. Either reproject with xugrid
   (`Ugrid2d.set_crs`, then `.ugrid.to_crs()`, which transforms the topology, not just relabels
   the arrays) or write real `*_lon` / `*_lat` variables and repoint `node_coordinates`,
   `edge_coordinates`, `face_coordinates` at them. Read the CRS from the grid file's own header;
   a registered EPSG code may use different units than the file (here feet versus metres).
3. **Triangles only.** `SCHISM_hgrid_face_nodes` is `(nface, 4)` padded with a fill value.
   Some viewers (gridlook) accept only `(nface, 3)`. Write a 3-column array with
   `start_index = 1` and repoint `face_node_connectivity`; refuse (or triangulate first) if
   the grid contains quads.
4. **String-typed mesh variable.** SCHISM writes `SCHISM_hgrid` as a 1-character string
   array. Zarr v3 records it with a data type zarrita cannot parse, so browser viewers
   silently fail mesh detection. Replace it with an `int32` scalar carrying the same attributes.
5. **Anonymous reads.** For a public store, flag the virtual chunk container anonymous, and
   allow the viewer's origin in the bucket's CORS.

Dimension names are `nSCHISM_hgrid_node`, `nSCHISM_hgrid_edge`, `nSCHISM_hgrid_face`;
vertical `nSCHISM_vgrid_layers`.

## Examples

- Private store: `scripts/build_virtual_icechunk.py`; public, viewer-friendly copy with
  lon/lat, triangles and the scalar mesh variable: `scripts/publish_public_icechunk.py`.
