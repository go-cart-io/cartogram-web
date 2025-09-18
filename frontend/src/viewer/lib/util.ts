export function addClipboard(button_id: string, message: string) {
  const icon_id = button_id + '-icon'
  navigator.clipboard.writeText(message)
  document.getElementById(icon_id)?.setAttribute('src', '/static/img/clipboard-check.svg')

  setTimeout(function () {
    document.getElementById(icon_id)?.setAttribute('src', '/static/img/clipboard.svg')
  }, 2000)
}

export function getGeojsonURL(
  currentMapName: string,
  mapDBKey: string | undefined,
  versionKey: string
) {
  // Figure out whether data is in userdata or cartdata
  const baseURL = mapDBKey ? '/userdata/' + mapDBKey + '/' : '/cartdata/' + currentMapName + '/'

  return '/static' + baseURL + versionKey
}

export function getCsvURL(currentMapName: string, mapDBKey: string | undefined) {
  const baseURL =
    mapDBKey && mapDBKey !== ''
      ? '/userdata/' + mapDBKey + '/'
      : '/cartdata/' + currentMapName + '/'

  return '/static' + baseURL + 'data.csv'
}
