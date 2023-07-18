setwd("D:\\Code\\cartogram-docker\\cartogram-web\\r") 

input = "OA_2011_London_gen_MHW.shp" #https://data.london.gov.uk/dataset/statistical-gis-boundary-files-london
output = "../data/test2"
  
is_random = TRUE

name_property = "ABR"
abbr_property = "ABR"
population_scale = c(100000, 5000000)

########################################################################################
library(sf)
oa <- st_read(input) 

if (is_random) {
  source("map_random.R")
  msoa_sf <- random_geography(oa, 1, FALSE)
  st_crs(msoa_sf) <- st_crs(oa)
} else {
  #TODO: Test this branch
  msoa_sf = oa
}

msoa_sf = msoa_sf[order(msoa_sf[[abbr_property]]),]

#Area
msoa_sf <- mutate(msoa_sf, area = as.vector(st_area(msoa_sf)))

#Population
if (is.null(msoa_sf$POPDEN)) {
  msoa_sf$populations = rep('', length(msoa_sf[[name_property]]))
} else {
  msoa_sf$populations <- msoa_sf$area * msoa_sf$POPDEN
}
if (exists("population_scale")) {
  library("scales")
  msoa_sf$populations <- rescale(msoa_sf$populations, to = population_scale)
}


#Label color
library(tmaptools)
mc <- map_coloring(msoa_sf, ncols = 6)
cb_set2 <- c("#66c2a5","#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f")
msoa_sf <- mutate(msoa_sf, color = cb_set2[mc])

#Label position
#https://stackoverflow.com/questions/74869220/how-to-force-text-displayed-by-the-tm-text-function-of-rs-tmap-to-remain-inside
df_points_within <- msoa_sf %>% 
  mutate(point_within = st_point_on_surface(geometry)) %>%
  as.data.frame() %>%
  select(-geometry) %>%
  st_as_sf()

#ID
msoa_sf$id = as.character(seq(1, length(msoa_sf[[abbr_property]]), 1))
msoa_sf$cartogram_id = as.character(seq(1, length(msoa_sf[[abbr_property]]), 1))

#Create template and data file
points_df <- as.data.frame(st_coordinates(df_points_within$point_within))
df = data.frame(msoa_sf$id, msoa_sf[[name_property]], msoa_sf[[abbr_property]], msoa_sf$color, points_df$X, points_df$Y, msoa_sf$area, msoa_sf$populations)
colnames(df) = c("Id", "Name", "Abbreviation", "Color", "Label.X", "Label.Y", "Area", "Population")
write.csv(df, paste0(output, ".csv"), row.names=FALSE)

#Create geojson
library(geojsonio)
if (name_property == abbr_property) {
  msoa_sf$name <- msoa_sf[[abbr_property]]
} else {
  msoa_sf$name <- msoa_sf[[name_property]]
}
msoa_selected_fields <- msoa_sf %>% select('geometry', 'id', 'cartogram_id', 'name')
outfile <- paste0(output, ".geojson")
st_write(msoa_selected_fields, outfile, append=FALSE, delete_dsn=TRUE, driver="GeoJSON", fid_column_name="id")

library(rjson)
msoa_json <- fromJSON(file = outfile)
bbox <- st_bbox(msoa_selected_fields)
msoa_json$bbox <- c(bbox$xmin[[1]], bbox$ymin[[1]], bbox$xmax[[1]], bbox$ymax[[1]])
msoa_json = toJSON(msoa_json)
write(msoa_json, outfile)

#Draw
library(tmap)
tm <- tm_shape(msoa_sf) + 
  tm_polygons(col = "color") + 
  tm_shape(df_points_within) + 
  tm_text(text = "ABR", legend.size.show = F)
tm_view(tm)

