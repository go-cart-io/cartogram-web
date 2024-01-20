# A script to create data file to be used with addmap.py
######################################################

input <- "../data/asean_processedmap.json"
output <- "../data/asean2"
name_property <- "NAME_0"
abbr_property <- "GID_0"

######################################################
library(this.path)
library(sf)
library(dplyr)
setwd(this.path::here())
map_sf <- st_read(input)
map_sf <- map_sf[order(map_sf[[name_property]]), ]

#Label color
library(tmaptools)
mc <- map_coloring(map_sf, ncols = 6)
cb_set2 <- c("#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f")
map_sf <- mutate(map_sf, color = cb_set2[mc])

#ID
map_sf$id <- as.character(seq(1, length(map_sf[[abbr_property]]), 1))
map_sf$cartogram_id <- as.character(seq(1, length(map_sf[[abbr_property]]), 1))

#Create template and data file
df <- data.frame(
  map_sf$id, map_sf[[name_property]], map_sf[[abbr_property]],
  map_sf$color, NA, NA)
colnames(df) <- c("Id", "Name", "Abbreviation", "Color", "Area", "Data")
write.csv(df, paste0(output, ".csv"), row.names=FALSE)

#Create geojson
library(geojsonio)
map_sf$name <- map_sf[[abbr_property]]
map_sf$ABR <- map_sf[[name_property]]
msoa_selected_fields <- map_sf %>% select('geometry', 'id', 'cartogram_id', 'name', 'ABR')
outfile <- paste0(output, ".geojson")
st_write(msoa_selected_fields, outfile, append=FALSE, delete_dsn=TRUE, driver="GeoJSON", 
         fid_column_name="id", layer_options = "RFC7946=YES")

library(rjson)
msoa_json <- fromJSON(file = outfile)
bbox <- st_bbox(msoa_selected_fields)
msoa_json$bbox <- c(bbox$xmin[[1]], bbox$ymin[[1]], bbox$xmax[[1]], bbox$ymax[[1]])
msoa_json <- toJSON(msoa_json)
write(msoa_json, outfile)
