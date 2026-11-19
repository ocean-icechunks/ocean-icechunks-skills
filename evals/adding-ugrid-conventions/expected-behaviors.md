# Expected behaviors: adding-ugrid-conventions

Grader's rubric. Do not show to the agent under evaluation.

## Across all scenarios

**Should**

- Add a mesh topology variable with `cf_role`, `topology_dimension`,
  `node_coordinates`, `face_node_connectivity`, and `face_dimension` where the
  connectivity is transposed.
- Set `start_index` to match the source (1 for FVCOM and SHYFEM).
- Verify by opening with `xugrid` and checking connectivity values against the
  node count, not only that it opens.
- Refuse to write to a production store; use a local or scratch store.
- Say what it checked and what it did not.

**Should not**

- Transpose a connectivity array in a virtual store.
- Treat "it opened without an error" as proof the mesh is right.
- Invent coordinates that the source does not hold.

## 1. FVCOM file

- Notices `nv` is `(three, nele)` and sets `face_dimension = "nele"`.
- Sets `start_index = 1` on `nv`.
- Adds `mesh` and `location` to data variables, and `UGRID-1.0` to `Conventions`.

## 2. SHYFEM output

- Reuses the existing `topology` variable instead of creating a second one.
- Points `face_node_connectivity` at `element_index`, with `start_index = 1`.

## 3. Virtual store

- Applies attributes to the in-memory virtual dataset, and writes the mesh
  topology variable into the store with zarr after `to_icechunk`, using
  `require_array`.
- Does not try to add a real variable to the virtual dataset before writing.

## 4. Opens but looks wrong

- Checks `start_index` first (a missing one does not raise an error) and the
  connectivity range against `n_node`, then the dimension order and
  `face_dimension`.

## 5. Static variables

- Says no: connectivity and bathymetry are data variables; promoting them to
  coordinates reclassifies them for every reader.
- Suggests handling them in the concat instead of by changing their role.

## 6. A SCHISM store that viewers cannot read

- Concatenates with `data_vars="minimal"` (and `coords="minimal"`) so static connectivity does
  not gain a time dimension; explains that as the xugrid error's cause.
- Handles the projected coordinates by reprojecting to lon/lat (xugrid `to_crs`, or real
  `*_lon`/`*_lat` variables with the mesh attributes repointed), reading the CRS from the grid
  file rather than guessing an EPSG code.
- Makes a 3-column triangle connectivity (`start_index = 1`) if the grid has no quads, and
  refuses or triangulates first if it does.
- Replaces a string-typed mesh variable with an `int32` scalar for browser viewers.
- Checks whether the output is already UGRID (`iof_ugrid`) before adding attributes.

## 7. ICON output

- Merges the separate grid file, renaming the data's dimensions to the grid's names first.
- Converts the radian coordinates to degrees with `units` and `standard_name` updated.
- Sets `start_index = 1` on `vertex_of_cell` and handles its `(3, ncells)` orientation
  (transposing in memory or `face_dimension`), and says the `face_dimension` route is untried
  on ICON.
- Uses the dataset's actual dimension names (not `ncells`/`nvertices` after a rename) when
  setting `mesh` and `location` on data variables.
- Subsets before plotting and warns that building the dataset takes a long time on large grids.
- Calls the ICON guidance Provisional.

## 8. ADCIRC forecast output

- Tries `xu.UgridDataset` on the file first and finds it needs no added attributes (the file
  carries `adcirc_mesh` and a face-first `element` array).
- Subsets the region before loading or plotting, because the global mesh has about 25 million
  elements.
- Does not invent metadata work that is not needed.

## 9. A model the skill has not been used on

- Applies the general pattern but states that Delft3D FM was not exercised by the skill.
- Checks the connectivity orientation and index base in the file rather than assuming another
  model's.
