# ADCIRC

Status: used on NOAA STOFS-2D Global output and on a `fort.14` mesh file (plotting only).

## Check first: the output may already be UGRID

NOAA STOFS-2D Global NetCDF files (`stofs_2d_glo_fcst.*.nc` in `s3://noaa-gestofs-pds`)
carry their own topology variable `adcirc_mesh`, the connectivity `element`
`(nele, nvertex=3)` (face-first), node coordinates `x`, `y` in degrees on dimension `node`,
and data variables such as `u-vel` `(time, node)`. In the example,
`xu.UgridDataset(xr.open_dataset(f, drop_variables="nvel"))` worked with no edits, so **do not
add attributes until you have tried xugrid.** The reason for dropping `nvel` was not recorded.
I did not inspect the attributes of `adcirc_mesh`; confirm `cf_role` and
`face_node_connectivity` there if xugrid does not find the mesh.

The global mesh is large (about 12.8 million nodes, 24.9 million elements); building the
`UgridDataset` took about 1.5 minutes, and subsetting with
`uds.ugrid.sel(x=slice(...), y=slice(...))` before plotting keeps it usable.

## Mesh files (`fort.14`)

A `fort.14` is plain text, not NetCDF: header, `ne nnodes`, then node lines
`(index, x, y, depth)` and element lines `(index, 3, n1, n2, n3)` with **1-based** node
indices. The example reads them into arrays by hand. That notebook only plots the mesh; it
does not add UGRID attributes. If you want a UGRID dataset from one, build the arrays, then
use `start_index = 1` on the connectivity.

## Examples

- STOFS-2D with xugrid and a Trimesh/Datashader plot:
  [gist](https://gist.github.com/rsignell/ebdbb0a3d814b9ca8be59b59fe738133).
- `fort.14` reader and plot: [gist](https://gist.github.com/rsignell/0859a63b2730c07aaad96d51b576e1b1).
