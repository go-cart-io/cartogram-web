# A script to calculate and visualize elongation ratio and convexity of each region, 
# to be criteria of data in our experiment
######################################################

setwd("D:\\Code\\cartogram-docker\\cartogram-web\\r")

input <- "../internal/static/cartdata/test6/2020.json"
#input2 <- "../internal/static/cartdata/test6/2016.json"
elongation_threshold <- 0.7
area_threshold <- 0.3
order_to_pick <- 5

######################################################
library(sf)
library(ggplot2)
library(patchwork)
library(Momocs)

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


calculate_elongation <- function(region) {
  points <- (st_coordinates(region))[,c("X","Y")]
  elongation <- coo_elongation(points)
  s_area <- st_area(region)
  area <- coo_area(points)
  chull_area <- coo_area(coo_chull(points))
  convexity <- coo_convexity(points)
  return (c(elongation, s_area, area, chull_area, convexity))
}

data_sf <- st_read(input)
elongation_list <- lapply(st_geometry(data_sf), calculate_elongation)
elongation_df <- do.call(rbind.data.frame, elongation_list)
colnames(elongation_df) <- c("elongation", "s_area", "area", "chull_area", "convexity")
data_sf <- cbind(data_sf, elongation_df)
# data_sf$is_elongate <- data_sf$elongation > elongation_threshold
# data_sf$area_ratio <- data_sf$area / data_sf$chull_area
# data_sf$is_curve <- data_sf$convexity < area_threshold

if (exists("input2")) {
  data_sf2 <- st_read(input2)
  elongation_list2 <- lapply(st_geometry(data_sf2), calculate_elongation)
  elongation_df2 <- do.call(rbind.data.frame, elongation_list2)
  colnames(elongation_df2) <- c("elongation", "s_area", "area", "chull_area", "convexity")
  data_sf2 <- cbind(data_sf2, elongation_df2)
  data_sf$elongation <- data_sf$elongation + data_sf2$elongation
  data_sf$convexity <- data_sf$convexity + data_sf2$convexity
}

# elongation_plot <- ggplot() +
#   geom_sf(data = data_sf, aes(fill = elongation))
# 
# area_ratio_plot <- ggplot() +
#   geom_sf(data = data_sf, aes(fill = area_ratio))
# 
# iselongation_plot <- ggplot() +
#   geom_sf(data = data_sf, aes(fill = is_elongate))
# 
# iscurve_plot <- ggplot() +
#   geom_sf(data = data_sf, aes(fill = is_curve))
# 
# (elongation_plot + area_ratio_plot) / (iselongation_plot + iscurve_plot)

# elongation_order <- data_sf[order(data_sf$elongation, decreasing = TRUE), ]
# convexity_order <- data_sf[order(data_sf$convexity), ]
# 
# elongation_order$ABR[order_to_pick]
# convexity_order$ABR[order_to_pick]

#ggplot(data_sf, aes(elongation, convexity)) + geom_point() + geom_text(aes(label = ABR))
data_sf <- mutate(data_sf, z_elong = scale(elongation)[, 1], z_convex = scale(convexity)[, 1])
ggplot(data_sf, aes(z_elong, z_convex)) + geom_point() + geom_text(aes(label = ABR)) + annotate("line", x = c(-2, 2), y = c(-2, 2)) + coord_equal()
