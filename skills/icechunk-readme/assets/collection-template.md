---
# Quote any value containing ' #' or ': ' ("issue #10"); YAML reads ' #' as a comment.
# Collection README source. Fill in, then render README.md and docs/documentation.md.
# Field rules (required, written by a person or filled from the store): assets/schema.yaml.
level: collection
title:                       # e.g. PacIOOS Hawaiʻi ocean, wave and weather models
source_coop:                 # every public URL is derived from these two
  account:                   # e.g. ocean-icechunks
  product:                   # e.g. pacioos
repository:                  # GitHub repo with the build code, notes and audit
provider:                    # who owns the source data; products inherit this
  name:                      # short, e.g. PacIOOS
  long_name:                 # e.g. Pacific Islands Ocean Observing System (PacIOOS)
  url:                       # provider home page
  data_services_url:         # provider's own data access page (header link)
  data_services_label:       # e.g. Data access (PacIOOS)
  citation_url:              # optional: how to cite the data; defaults to data_services_url
viewer:                      # optional: the one browser viewer for the whole collection
  name:                      # link text, e.g. Gridlook
  url:                       # .../viewer/index.html
  project_url:               # viewer project, for credits
  fork_url:                  # fork the published copy is built from, if any
products:                    # product ids in table order; each has its own source file
  -
code_license:                # for the build code; the data license is the provider's
  spdx:                      # e.g. Apache-2.0
  author:                    # e.g. E. E. Holmes
  attribution_required:      # true | false
credits:                     # {label, text}; Markdown allowed in text
  - label: Data
    text:
  - label: Icechunk packaging
    text:
  - label: Tooling           # keep; add contributors after Rich Signell in contribution order
    text: >-
      [ocean-icechunks-skills](https://github.com/ocean-icechunks/ocean-icechunks-skills), agent skills
      for building and documenting Icechunk stores, by Eli Holmes, Rich Signell and
      [other contributors](https://github.com/ocean-icechunks/ocean-icechunks-skills/graphs/contributors).
netcdf_layout:               # optional, e.g. <dataset>/netcdf/[<version>/]<year>/<file>.nc
---

# README

## Summary

<!-- Required. One or two sentences: what the data are and who makes them. -->

## Citation

<!-- Optional; delete to use the generated sentence ("The data are <provider>'s. Any use
     ... should cite <provider>, as described at <citation_url>."). -->

## Caveats

<!-- Optional; delete if empty. Known gaps a reader must see before using the data. -->

# Documentation

<!-- Required. Free sections, rendered in order to docs/documentation.md. Recommended:
     About the data; The Icechunk stores; The viewer; NetCDF copies;
     Known problems in the files; How this was built. -->

## About the data

## How this was built
