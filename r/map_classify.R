setwd("D:\\Code\\cartogram-docker\\cartogram-web\\r")

input <- "../internal/static/cartdata/test3/population.json"
elongation_threshold <- 0.7
area_threshold <- 0.3

######################################################
library(sf)
library(ggplot2)
library(patchwork)
data_sf <- st_read(input)

# Function to calculate the minimum bounding box of a region
#calculate_min_bounding_box <- function(region) {
#  bbox <- st_bbox(region)
#  return (bbox)
  #return(st_as_sfc(bbox, crs = st_crs(region)))
#}

# Calculate and save the minimum bounding box as a new column in the sf object
#bbox_list <- lapply(st_geometry(data_sf), calculate_min_bounding_box)
#bbox_df <- do.call(rbind.data.frame, bbox_list)
#colnames(bbox_df) <- c("xmin", "ymin", "xmax", "ymax")

# Combine the bounding box data with the original data_sf
#data_sf <- cbind(data_sf, bbox_df)

# Plot all regions and their bounding boxes
#ggplot() +
#  geom_sf(data = data_sf, color = "blue", fill = "transparent") +
#  geom_rect(data = bbox_df, aes(xmin = xmin, ymin = ymin, xmax = xmax, ymax = ymax), 
#            color = "red", linetype = "dashed", fill = NA)

#rotated_rect <- st_minimum_rotated_rectangle(data_sf)
#ggplot() +
#  geom_sf(data = data_sf, color = "blue", fill = "transparent") +  
#  geom_sf(data = rotated_rect, color = "red", fill = "transparent")

library(Momocs)
calculate_elongation <- function(region) {
  points <- (st_coordinates(region))[,c("X","Y")]
  elongation <- coo_elongation(points)
  s_area <- st_area(region)
  area <- coo_area(points)
  chull_area <- coo_area(coo_chull(points))
  return (c(elongation, s_area, area, chull_area))
}

elongation_list <- lapply(st_geometry(data_sf), calculate_elongation)
elongation_df <- do.call(rbind.data.frame, elongation_list)
colnames(elongation_df) <- c("elongation", "s_area", "area", "chull_area")
data_sf <- cbind(data_sf, elongation_df)
data_sf$is_elongate <- data_sf$elongation > elongation_threshold
data_sf$area_ratio <- data_sf$area / data_sf$chull_area
data_sf$is_curve <- data_sf$area_ratio < area_threshold

elongation_plot <- ggplot() +
  geom_sf(data = data_sf, aes(fill = elongation))

area_ratio_plot <- ggplot() +
  geom_sf(data = data_sf, aes(fill = area_ratio))

iselongation_plot <- ggplot() +
  geom_sf(data = data_sf, aes(fill = is_elongate))

iscurve_plot <- ggplot() +
  geom_sf(data = data_sf, aes(fill = is_curve))

(elongation_plot + area_ratio_plot) / (iselongation_plot + iscurve_plot)
