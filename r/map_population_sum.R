# A script for summarizing detailed yearly population data from 
# https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/adhocs/13946censusoutputareapopulationestimatesformid2001tomid2020supportinginformation
# to yearly population data

######################################################

input <- "raw_data/Output_Area_Pop_est_2016_20.csv"
output <- "raw_data/Output_Area_Pop_est_SUM.csv"

######################################################
population_df <- read.csv(input)

library(dplyr)
agg_tbl <- population_df %>% 
  group_by(OA11CD) %>%
  summarise(across(c(mid_2016,mid_2017,mid_2018,mid_2019,mid_2020), sum), .groups = 'drop')  %>%
  as.data.frame()

write.csv(agg_tbl, output, row.names=FALSE)
