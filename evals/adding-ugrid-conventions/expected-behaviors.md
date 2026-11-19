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

## 5. A model the skill has not been used on

- Applies the general pattern but states that SCHISM was not exercised by the skill.
- Checks the connectivity orientation and index base in the file rather than assuming FVCOM's.
