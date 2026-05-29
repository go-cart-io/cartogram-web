export {}

interface CartogramConfig {
  mode?: string
  maps: CMapHandlers
  mapName?: string
  mapTitle?: string
  mapDBKey?: string
  cartoVersions: {
    [key: string]: {
      header: string
      key: string
      name: string
      unit: string
      type?: 'noncontiguous' | 'contiguous' | 'choropleth' // 'type' is optional as seen in key "0"
    }
  }
  cartoEqualAreaBg?: boolean
  cartoColorScheme?: string
  choroVersions?: Array<string>
  choroSpec?: any
  maxCartogram?: number
}

declare global {
  interface Window {
    gtag: (...args: any[]) => void
    CARTOGRAM_CONFIG: CartogramConfig
  }
}
