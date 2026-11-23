# NOAA OISST v2.1 daily sea surface temperature: global metadata attributes

_Generated from the store on each update. Do not edit by hand; `ds.attrs` shows the current set._

## Published Icechunk dataset

Store: [https://data.source.coop/ocean-icechunks/noaa-oisst/oisst.icechunk](https://data.source.coop/ocean-icechunks/noaa-oisst/oisst.icechunk); snapshot <code>Z0RZCMCJM9TMVS2ECABG</code>.

The root group has no attributes; each group has its own.

### Group `/daily`

| Attribute | Value |
|---|---|
| <code>Conventions</code> | <code>CF-1.6, ACDD-1.3</code> |
| <code>Description</code> | <code>Reynolds, et al.(2007) Daily High-resolution Blended Analyses. Available at ftp://eclipse.ncdc.noaa.gov/pub/OI-daily/daily-sst.pdf  Climatology is based on 1971-2000 OI.v2 SST, Satellite data: Navy  NOAA19 METOP AVHRR, Ice data: NCEP ice</code> |
| <code>cdm&#95;data&#95;type</code> | <code>Grid</code> |
| <code>comment</code> | <code>Data was converted from NetCDF-3 to NetCDF-4 format with metadata updates in November 2017.</code> |
| <code>coordinates</code> | <code>time zlev lat lon preliminary</code> |
| <code>creator&#95;email</code> | <code>oisst-help@noaa.gov</code> |
| <code>creator&#95;url</code> | <code>https://www.ncei.noaa.gov/</code> |
| <code>date&#95;created</code> | <code>2026-11-17T14:31:00Z</code> |
| <code>date&#95;modified</code> | <code>2026-11-17T14:31:00Z</code> |
| <code>geospatial&#95;lat&#95;max</code> | <code>90.0</code> |
| <code>geospatial&#95;lat&#95;min</code> | <code>-90.0</code> |
| <code>geospatial&#95;lat&#95;resolution</code> | <code>0.25</code> |
| <code>geospatial&#95;lat&#95;units</code> | <code>degrees&#95;north</code> |
| <code>geospatial&#95;lon&#95;max</code> | <code>360.0</code> |
| <code>geospatial&#95;lon&#95;min</code> | <code>0.0</code> |
| <code>geospatial&#95;lon&#95;resolution</code> | <code>0.25</code> |
| <code>geospatial&#95;lon&#95;units</code> | <code>degrees&#95;east</code> |
| <code>history</code> | <code>Final file created using preliminary as first guess, and 3 days of AVHRR data. Preliminary uses only 1 day of AVHRR data.</code> |
| <code>id</code> | <code>oisst-avhrr-v02r01.20261116&#95;preliminary.nc</code> |
| <code>institution</code> | <code>NOAA/National Centers for Environmental Information</code> |
| <code>instrument</code> | <code>Earth Remote Sensing Instruments &gt; Passive Remote Sensing &gt; Spectrometers/Radiometers &gt; Imaging Spectrometers/Radiometers &gt; AVHRR &gt; Advanced Very High Resolution Radiometer</code> |
| <code>instrument&#95;vocabulary</code> | <code>Global Change Master Directory (GCMD) Instrument Keywords</code> |
| <code>keywords</code> | <code>Earth Science &gt; Oceans &gt; Ocean Temperature &gt; Sea Surface Temperature</code> |
| <code>keywords&#95;vocabulary</code> | <code>Global Change Master Directory (GCMD) Earth Science Keywords</code> |
| <code>metadata&#95;link</code> | <code>https://doi.org/10.25921/RE9P-PT57</code> |
| <code>naming&#95;authority</code> | <code>gov.noaa.ncei</code> |
| <code>ncei&#95;template&#95;version</code> | <code>NCEI&#95;NetCDF&#95;Grid&#95;Template&#95;v2.0</code> |
| <code>platform</code> | <code>Ships, buoys, Argo floats, MetOp-A, MetOp-B</code> |
| <code>platform&#95;vocabulary</code> | <code>Global Change Master Directory (GCMD) Platform Keywords</code> |
| <code>processing&#95;level</code> | <code>NOAA Level 4</code> |
| <code>product&#95;version</code> | <code>Version v02r01</code> |
| <code>references</code> | <code>Reynolds, et al.(2007) Daily High-Resolution-Blended Analyses for Sea Surface Temperature (available at https://doi.org/10.1175/2007JCLI1824.1). Banzon, et al.(2016) A long-term record of blended satellite and in situ sea-surface temperature for climate monitoring, modeling and environmental studies (available at https://doi.org/10.5194/essd-8-165-2016). Huang et al. (2020) Improvements of the Daily Optimum Interpolation Sea Surface Temperature (DOISST) Version v02r01, submitted.Climatology is based on 1971-2000 OI.v2 SST. Satellite data: Pathfinder AVHRR SST, Navy AVHRR SST, and NOAA ACSPO SST. Ice data: NCEP Ice and GSFC Ice.</code> |
| <code>sensor</code> | <code>Thermometer, AVHRR</code> |
| <code>source</code> | <code>ICOADS, NCEP&#95;GTS, GSFC&#95;ICE, NCEP&#95;ICE, Pathfinder&#95;AVHRR, Navy&#95;AVHRR, NOAA&#95;ACSP</code> |
| <code>standard&#95;name&#95;vocabulary</code> | <code>CF Standard Name Table (v40, 25 January 2017)</code> |
| <code>summary</code> | <code>NOAAs 1/4-degree Daily Optimum Interpolation Sea Surface Temperature (OISST) (sometimes referred to as Reynolds SST, which however also refers to earlier products at different resolution), currently available as version v02r01, is created by interpolating and extrapolating SST observations from different sources, resulting in a smoothed complete field. The sources of data are satellite (AVHRR) and in situ platforms (i.e., ships and buoys), and the specific datasets employed may change over time. At the marginal ice zone, sea ice concentrations are used to generate proxy SSTs.  A preliminary version of this file is produced in near-real time (1-day latency), and then replaced with a final version after 2 weeks. Note that this is the AVHRR-ONLY DOISST, available from Oct 1981, but there is a companion DOISST product that includes microwave satellite data, available from June 2002</code> |
| <code>time&#95;coverage&#95;end</code> | <code>2026-11-16T23:59:59Z</code> |
| <code>time&#95;coverage&#95;start</code> | <code>2026-11-16T00:00:00Z</code> |
| <code>title</code> | <code>NOAA/NCEI 1/4 Degree Daily Optimum Interpolation Sea Surface Temperature (OISST) Analysis, Version 2.1 - Inter</code> |

### Group `/monthly`

| Attribute | Value |
|---|---|
| <code>Conventions</code> | <code>CF-1.6, ACDD-1.3</code> |
| <code>creator&#95;name</code> | <code>NERACOOS / GMRI</code> |
| <code>geospatial&#95;lat&#95;max</code> | <code>90.0</code> |
| <code>geospatial&#95;lat&#95;min</code> | <code>-90.0</code> |
| <code>geospatial&#95;lat&#95;resolution</code> | <code>0.25</code> |
| <code>geospatial&#95;lat&#95;units</code> | <code>degrees&#95;north</code> |
| <code>geospatial&#95;lon&#95;max</code> | <code>360.0</code> |
| <code>geospatial&#95;lon&#95;min</code> | <code>0.0</code> |
| <code>geospatial&#95;lon&#95;resolution</code> | <code>0.25</code> |
| <code>geospatial&#95;lon&#95;units</code> | <code>degrees&#95;east</code> |
| <code>history</code> | <code>Monthly statistics computed from the daily/ group of this store by ohw26&#95;oisst&#95;icechunk.</code> |
| <code>institution</code> | <code>NERACOOS / Gulf of Maine Research Institute</code> |
| <code>platform</code> | <code>Ships, buoys, Argo floats, MetOp-A, MetOp-B</code> |
| <code>references</code> | <code>Reynolds, et al.(2007) Daily High-Resolution-Blended Analyses for Sea Surface Temperature (available at https://doi.org/10.1175/2007JCLI1824.1). Banzon, et al.(2016) A long-term record of blended satellite and in situ sea-surface temperature for climate monitoring, modeling and environmental studies (available at https://doi.org/10.5194/essd-8-165-2016). Huang et al. (2020) Improvements of the Daily Optimum Interpolation Sea Surface Temperature (DOISST) Version v02r01, submitted.Climatology is based on 1971-2000 OI.v2 SST. Satellite data: Pathfinder AVHRR SST, Navy AVHRR SST, and NOAA ACSPO SST. Ice data: NCEP Ice and GSFC Ice.</code> |
| <code>sensor</code> | <code>Thermometer, AVHRR</code> |
| <code>source</code> | <code>NOAA OISST v2.1 daily AVHRR-only final files</code> |
| <code>summary</code> | <code>Monthly minimum, maximum, mean and standard deviation of final daily NOAA OISST v2.1 fields, computed by this project from the daily/ group. Not a NOAA product.</code> |
| <code>title</code> | <code>NOAA Optimum Interpolation SST v2.1 monthly statistics</code> |
