# A script to calculate and visualize elongation ratio and convexity of each region, 
# to be criteria of data in our experiment
######################################################

setwd("D:\\Code\\cartogram-docker\\cartogram-web\\r")

base <- "../internal/static/cartdata/test58"
input <- paste0(base, "/2020.json")
#input2 <- paste0(base, "/2016.json")
elong_e_min <- 0.7
elong_c_min <- 0.8
curve_e_max <- 0.5
curve_c_max <- 0.7

######################################################
library(sf)
library(ggplot2)
library(patchwork)
library(Momocs)

calculate_elongation <- function(region) {
  points <- (st_coordinates(region))[,c("X","Y")]
  elongation <- round(coo_elongation(points), digits = 3)
  #s_area <- st_area(region)
  #area <- coo_area(points)
  #chull_area <- coo_area(coo_chull(points))
  convexity <- round(coo_convexity(points), digits = 3)
  return (c(elongation, convexity))
}

data_sf <- st_read(input)
elongation_list <- lapply(st_geometry(data_sf), calculate_elongation)
elongation_df <- do.call(rbind.data.frame, elongation_list)
colnames(elongation_df) <- c("elongation", "convexity")
data_sf <- cbind(data_sf, elongation_df)

if (exists("input2")) {
  data_sf2 <- st_read(input2)
  elongation_list2 <- lapply(st_geometry(data_sf2), calculate_elongation)
  elongation_df2 <- do.call(rbind.data.frame, elongation_list2)
  colnames(elongation_df2) <- c("elongation", "convexity")
  data_sf2 <- cbind(data_sf2, elongation_df2)
  data_sf$elongation <- (data_sf$elongation + data_sf2$elongation) / 2
  data_sf$convexity <- (data_sf$convexity + data_sf2$convexity) / 2
}

data_sf$type <- ifelse(data_sf$elongation > elong_e_min & data_sf$convexity > elong_c_min, 'elong', 'normal')
data_sf$type <- ifelse(data_sf$elongation < curve_e_max & data_sf$convexity < curve_c_max, 'curve', data_sf$type)

#map_plot <- ggplot() +
#  geom_sf(data = data_sf, aes(fill = color)) #+
#  geom_sf_label(aes(label = ABR))

map_plot <- ggplot(data_sf) +
  geom_sf(aes(fill = type)) +
  geom_sf_label(aes(label = ABR))

 
# elongation_order <- data_sf[order(data_sf$elongation, decreasing = TRUE), ]
# convexity_order <- data_sf[order(data_sf$convexity), ]
# 
# elongation_order$ABR[order_to_pick]
# convexity_order$ABR[order_to_pick]

#ggplot(data_sf, aes(elongation, convexity)) + geom_point() + geom_text(aes(label = ABR))
data_sf <- mutate(data_sf, z_elong = scale(elongation)[, 1], z_convex = scale(convexity)[, 1])
relation_plot <- ggplot(data_sf, aes(z_elong, z_convex)) + geom_point() + geom_text(aes(label = ABR)) + annotate("line", x = c(-2, 2), y = c(-2, 2)) + coord_equal()

map_plot + relation_plot

info <- subset(data_sf, ABR == 'SL' | ABR == 'SD', select = c('ABR','elongation','convexity'))
info
st_distance(info)
