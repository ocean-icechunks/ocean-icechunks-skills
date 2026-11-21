---
# Quote any value containing ' #' or ': ' ("issue #10"); YAML reads ' #' as a comment.
# Product README source. Fill in, then render README.md, docs/documentation.md and
# docs/metadata.md. Field rules: assets/schema.yaml. Variables, coordinates, groups,
# snapshot, last update and global attributes are read from the store: do not write them here.
# Provider, repository, code license and viewer URL are inherited from the collection.
level: product
id:                          # folder name under the collection, e.g. roms_hiig
collection: ../collection.md # relative path to the collection source file
title:                       # e.g. PacIOOS ROMS Hawaiʻi forecast: Icechunk store, best time series
row:                         # this product's row in the collection tables
  name:                      # e.g. ROMS ocean forecast
  detail:                    # e.g. daily runs
  short_name:                # e.g. ROMS forecast, best time series
  store_note:                # optional, e.g. best time series
store_url:                   # public HTTPS URL of the Icechunk store
netcdf_url:                  # optional: public prefix of the NetCDF copies
provider_page:               # optional header link
  label:                     # e.g. PacIOOS dataset page
  url:
viewer:                      # required if the collection has a viewer
  variable:                  # variable shown first, e.g. temp
  view:                      # viewer state, e.g. px=0::py=0::alt=4000000::lat=20.5::lon=-158.2::dimIndices_time=0
  fields:                    # optional per-variable table in documentation: {label, variable, view?}
    -
groups_note:                 # required if the store has more than one group: why it is split
coordinate_notes:            # optional: name -> plain-language Values cell, replacing the auto range
variable_notes:              # optional: name -> text when a variable has no standard_name
code:
  python:
    python_version:          # minimum, e.g. "3.12"
    packages:                # e.g. [icechunk >= 2.3, xarray, zarr]
    pip:                     # e.g. pip install "icechunk>=2.3" xarray zarr
    function:                # loader name, e.g. open_forecast
    docstring:               # one line
    concurrency:             # zarr async.concurrency the timings used, e.g. 128
    chunks_advice:           # optional: replaces the standard "open with chunks=None, subset, then chunk" comment
    dask_example:            # sentence pointing to the example that subsets then chunks, e.g. The last example below does this.
access:                      # only when reads are NOT anonymous public HTTPS
  auth:                      # credentials needed, and how to get them
  region:                    # compute-region or network limits
performance:                 # measured, never estimated
  rows:                      # {read, chunks, data_moved, time}
    -
  measured:                  # when, where and with which settings
provenance:
  built:                     # date of the first build
  build_script:              # e.g. build_store.py
  build_url:                 # link to it in the repository
  tested_with:               # versions the README code was run with
  build_files:               # file names published in docs/; or {file, label}
    -
  how_made:                  # how_store_created.md
    file:
    url:
  plan:                      # planning issue
    label:
    url:
citation_extra:              # optional, e.g. who runs the model
metadata:
  netcdf_attributes: false   # true adds the latest NetCDF file's attributes to metadata.md
extra_sections:              # escape hatch, only when no field fits; say why
---

# README

## Summary

<!-- Required. What the store is: model, region, resolution, cadence.
     The store URL is placed after it automatically. -->

## Notes

<!-- Optional. Short paragraphs a reader needs before the tables,
     e.g. what "best time series" means. -->

## Variable notes

<!-- Optional. Short lines after the tables, e.g. "Land reads as NaN." -->

## Example analyses

<!-- Required. One code block per language, run against the store; a comment on each step.
     It follows the generated loading code, so `ds` already exists. Include one example that
     subsets and then calls .chunk(), and point to it with code.python.dask_example. -->

## Source files

<!-- Required. One paragraph: what the files are, how they were copied, coverage and gaps. -->

## Caveats

<!-- Optional; delete if empty. Known gaps or anything unverified. -->

# Documentation

<!-- Required. Free sections, rendered in order to docs/documentation.md.
     {{viewer_fields_table}} is replaced by the per-variable viewer table. Recommended:
     A virtual store (required); What the store adds over the files; The viewer;
     Where the metadata came from; The time axis; Opening the store: notes;
     Performance: why reads cost what they do; How the store was built and validated; Updates. -->

## A virtual store
