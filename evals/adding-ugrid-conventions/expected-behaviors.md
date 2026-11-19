# Expected behaviors: adding-ugrid-conventions

Grader's rubric. Do not show to the agent under evaluation.

## Across all scenarios

**Should**

- Inspect the file's actual variable and dimension names before proposing attributes.
- Verify with `xugrid.UgridDataset`: node and face counts match the file, and one plotted field
  looks like the model domain.
- Say that the guidance is Experimental and comes from FVCOM and SHYFEM.

**Should not**

- Transpose a connectivity array that lives in a virtual store.
- Treat static arrays (`nv`, bathymetry) as coordinates.
- Write to a production store to test the change.

## 1. xugrid does not recognise an FVCOM store

- Adds a scalar mesh topology variable with `cf_role = "mesh_topology"`,
  `topology_dimension = 2`, `node_coordinates`, `face_coordinates`,
  `face_node_connectivity` and `face_dimension = "nele"`.
- Sets `cf_role` and `start_index = 1` on `nv`; sets `mesh` and `location` on each data variable
  (from its dimension: `nele` is face, `node` is node); appends UGRID to `Conventions`.
- Explains that `face_dimension` is how the `(three, nele)` orientation is handled.

## 2. Triangles shifted by one node

- Identifies the missing `start_index = 1` (FVCOM connectivity is 1-based) as the cause.
- Does not suggest rewriting the connectivity values.

## 3. SHYFEM output

- Reuses the existing `topology` variable as the mesh topology variable and names
  `element_index` as the connectivity; sets `start_index = 1`.
- Does not copy FVCOM names (`nv`, `nele`) without checking the file.

## 4. The store is already written

- Writes `mesh_topology` as an ordinary Zarr array after `to_icechunk` and before the commit,
  using `require_array` so re-runs do not fail; applies the other attributes in the Zarr
  metadata.
- Does not claim the variable can be added to the virtual dataset before writing.

## 5. A SCHISM store that viewers cannot read

- Concatenates with `data_vars="minimal"` (and `coords="minimal"`) so static connectivity does
  not gain a time dimension; explains that as the xugrid error's cause.
- Handles the projected coordinates by reprojecting to lon/lat (xugrid `to_crs`, or real
  `*_lon`/`*_lat` variables with the mesh attributes repointed), reading the CRS from the grid
  file rather than guessing an EPSG code.
- Makes a 3-column triangle connectivity (`start_index = 1`) if the grid has no quads, and
  refuses or triangulates first if it does.
- Replaces a string-typed mesh variable with an `int32` scalar for browser viewers.
- Checks whether the output is already UGRID (`iof_ugrid`) before adding attributes.

## 6. ICON output

- Merges the separate grid file, renaming the data's dimensions to the grid's names first.
- Converts the radian coordinates to degrees with `units` and `standard_name` updated.
- Sets `start_index = 1` on `vertex_of_cell` and handles its `(3, ncells)` orientation
  (transposing in memory or `face_dimension`), and says the `face_dimension` route is untried
  on ICON.
- Uses the dataset's actual dimension names (not `ncells`/`nvertices` after a rename) when
  setting `mesh` and `location` on data variables.
- Subsets before plotting and warns that building the dataset takes a long time on large grids.
- Calls the ICON guidance Provisional.

## 7. ADCIRC forecast output

- Tries `xu.UgridDataset` on the file first and finds it needs no added attributes (the file
  carries `adcirc_mesh` and a face-first `element` array).
- Subsets the region before loading or plotting, because the global mesh has about 25 million
  elements.
- Does not invent metadata work that is not needed.

## 8. A model the skill has not been used on

- Applies the general pattern but states that Delft3D FM was not exercised by the skill.
- Checks the connectivity orientation and index base in the file rather than assuming another
  model's.
