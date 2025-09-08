import type { Spec } from 'vega'

export type StringObject = { [key: string]: string | undefined }

export interface CMapHandlers {
  [key: string]: { name: string }
}

export interface CSettingSpec extends Spec {
  legend_titles?: StringObject
}
