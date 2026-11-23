---
# Partial source file: only the fields the collection tables need. The full product
# README is not rendered from it yet; that needs a markup pass on this product.
level: product
id: wrf_hi
collection: collection.md
title: "WRF Regional Atmospheric Model: Main Hawaiian Islands Forecast"
row:
  name: WRF weather model
  detail: "daily runs"
  short_name: WRF forecast, best time series
  store_note: hourly best time series
store_url: https://data.source.coop/ocean-icechunks/pacioos/wrf_hi/icechunk
source_url: https://data.source.coop/ocean-icechunks/pacioos/wrf_hi/netcdf/
viewer:
  variable: Tair
  view: px=0::py=0::alt=4000000::lat=20.5::lon=-158.2::dimIndices_time=0
code:
  python: {}
---
