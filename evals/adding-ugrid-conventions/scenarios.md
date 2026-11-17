# Evaluation scenarios: adding-ugrid-conventions

Give the agent one scenario at a time, with no other context. None of these may
write to a production Icechunk repository, dataset, or object store; any
execution must target a local temporary directory or an explicitly scratch
prefix.

## 1. An FVCOM file that xugrid cannot read

> Here is an FVCOM NetCDF file. It has `lon`, `lat`, `lonc`, `latc`, `h` and a
> connectivity array `nv` with dimensions `(three, nele)`. `xugrid` cannot open
> it as a mesh. Make it UGRID so that it can.

## 2. SHYFEM output with a topology placeholder

> SHYFEM output has a `topology` variable, an `element_index` array of triangle
> node numbers, and `longitude` and `latitude`. Make it work with `xugrid`.

## 3. Mesh data in a virtual Icechunk store

> We build a virtual Icechunk store from many FVCOM files. The source has no mesh
> topology variable. Add UGRID so readers can use `xugrid` on the store.

## 4. A mesh that opens but looks wrong

> A teammate added UGRID attributes to ADCIRC-style output. `xugrid` opens it
> without an error, but the plot is a scramble of triangles. What should we check?

## 5. Protecting static variables

> While concatenating files we want `nv` and `h` to stay out of the concat. Should
> we mark them as coordinates?
