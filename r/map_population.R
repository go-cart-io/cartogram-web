# A script to put population data over years into template, to be used with addmap2.py
######################################################

setwd("D:\\Code\\cartogram-docker\\cartogram-web\\r")

template_input <- "../data/test22.csv"
yearly_input <- "raw_data/Output_Area_Pop_est_SUM.csv"
population_power <- 4

######################################################
library(dplyr)
template_df <- read.csv(template_input)
population_df <- read.csv(yearly_input)

df <- left_join(template_df, population_df, by=c('Name'='OA11CD'))

for (colname in 2016:2020) {
  ori_colname <- paste0('mid_', colname) 
  new_colname <- paste0('', colname) 
  mean_col <- mean(df[[ori_colname]])
  df[new_colname] <- round(((df[ori_colname] / mean_col) ^ population_power) * 1000)
}

df <- subset(df, select = -c(Population,mid_2016,mid_2017,mid_2018,mid_2019,mid_2020))

write.csv(template_df, paste0(template_input, '.bak'), row.names=FALSE)
write.csv(df, template_input, row.names=FALSE)
