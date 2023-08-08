# A script to randomly select middle output area
# Adapted from Yau Yen Ching code
######################################################

library(sf)
library(purrr)
library(dplyr)
library(stringr)

check_multipolygon <- function(object) {
  all(st_is(object, "MULTIPOLYGON"))
}

available_letters <- LETTERS
two_letters <- c()
for (i in 1:length(available_letters)) {
  for (j in 1:length(available_letters)) {
    combination <- paste(available_letters[i], available_letters[j], sep = "")
    two_letters <- c(two_letters, combination)
  }
}

generate_labelled_sf <- function(msoas, num, msoa) {
  selected <- sample(msoas, 1)
  sf <- oa[oa$MSOA11NM == selected,]
  st_crs(sf) <- NA
  if (!msoa) {
    sample <- sf$LSOA11NM %>% unique()
    repeat {
      lsoas <- sample(sample, 2)
      lsoa_1 <- sf %>% filter(LSOA11NM == lsoas[1])
      lsoa_2 <- sf %>% filter(LSOA11NM == lsoas[2])
      contiguous <-
        (map_int(st_touches(lsoa_1, lsoa_2), length) > 0) %>% any()
      
      if (contiguous) {
        if (!check_multipolygon(lsoa_1) | !check_multipolygon(lsoa_2)) {
          generate_labelled_sf(msoas, num, msoa)
        }
        sf <- rbind(lsoa_1, lsoa_2)
        break
      }
    }
  }
  sf['component'] <- num
  sf
}

#num_components the number of components to generate
#is_small_oa a boolean indicating whether to generate small areas
random_geography <- function(oa, num_components, is_small_oa) {
  msoas <- oa$MSOA11NM %>% unique()
  selected_msoa <- sample(msoas, 1)
  msoa_sf <- oa[oa$MSOA11NM == selected_msoa,]
  st_crs(msoa_sf) <- NA

  if (!check_multipolygon(msoa_sf)) random_geography(num_components, is_small_oa) #modified
  
  if (num_components > 1) {
    st_crs(msoa_sf) <- NA
    msoa_sf['component'] <- 1

    if (num_components == 2) {
      result <- rbind(msoa_sf, generate_labelled_sf(msoas, 2, TRUE))
    } else {
      result <- rbind(
        msoa_sf,
        generate_labelled_sf(msoas, 2, FALSE),
        generate_labelled_sf(msoas, 3, FALSE)
      )
    }
    result['ABR'] <- sample(x = two_letters, size = nrow(result))
    #replicate(nrow(result), paste0(sample(available_letters, 2, replace = FALSE), collapse = ""))
    return(result)
  }
  
  if (length(msoa_sf) >= 40 | is_small_oa) {
    return (msoa_sf)
  } else {
    msoa_name <- str_split(selected_msoa, "\\s\\d")[[1]]
    name <- msoa_name[1]
    code <- msoa_name[2] %>% as.numeric()
    helper <- function(msoa_1) {
      code_range <- c(1,-1, 2,-2, 3,-3, 4,-4, 5,-5)
      for (i in code_range) {
        test_code <- (code + i) %>% str_pad(3, side = "left", pad = "0")
        test_msoa <- str_c(name, test_code, sep = " ")
        if (test_msoa %in% msoas) {
          msoa_2 <- oa[oa$MSOA11NM == test_msoa,]
          st_crs(msoa_2) <- NA
          contiguous <-
            (map_int(st_touches(msoa_1, msoa_2), length) > 0) %>% any()
          if (contiguous & check_multipolygon(msoa_2)) {
            return(msoa_2)
          }
        }
      }
      return (NULL)
    }
    msoa_sf_2 <- helper(msoa_sf)
    if (!is.null(msoa_sf_2)) {
      result <- rbind(msoa_sf, msoa_sf_2)
      result['ABR'] <- sample(x = two_letters, size = nrow(result))
      return(result)
    } else {
      random_geography(num_components, is_small_oa)
    }
  }
}
