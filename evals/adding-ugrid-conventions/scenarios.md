# Evaluation scenarios: adding-ugrid-conventions

Give the agent one scenario at a time, with no other context. None of these may write to a
production store; any write must target an explicitly scratch store or prefix.

## 1. xugrid does not recognise an FVCOM store

> I built a virtual Icechunk store from NECOFS FVCOM NetCDF files. `xr.open_zarr` works, but
> `xu.UgridDataset(ds)` says there is no mesh. The file has `lon`, `lat`, `lonc`, `latc` and
> `nv` with dimensions `(three, nele)`. What do I add?

## 2. Triangles shifted by one node

> I added `cf_role = "face_node_connectivity"` to `nv` and xugrid opens it, but the plot shows
> scrambled triangles with a hole at the edge. The connectivity is from an FVCOM file.

## 3. SHYFEM output

> Add UGRID metadata to this SHYFEM output so hvplot can plot temperature. There is a scalar
> variable `topology` and a connectivity array `element_index`.

## 4. The store is already written

> The Icechunk store is already built and committed. I want to add the mesh variable without
> rebuilding everything.

## 5. A SCHISM store that viewers cannot read

> I built a virtual Icechunk store from SCHISM `out2d` and per-variable NetCDF files. xugrid
> says a connectivity array has an unexpected extra dimension, and a browser viewer finds no
> mesh. The coordinates are in State Plane metres and `SCHISM_hgrid_face_nodes` has four
> columns.

## 6. ICON output

> I have ICON ocean output as a Zarr reference plus a separate grid Zarr. Make it work with
> xugrid. The coordinates are `clon`, `clat`, `vlon`, `vlat` and the connectivity is
> `vertex_of_cell` with shape `(3, ncells)`.

## 7. ADCIRC forecast output

> Open the latest NOAA STOFS-2D Global NetCDF with xugrid and plot water velocity for the
> Chesapeake Bay region. Do whatever metadata work is needed.

## 8. A model the skill has not been used on

> Prepare this Delft3D FM output so xugrid recognises the mesh.
