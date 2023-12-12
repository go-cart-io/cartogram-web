//import Tracker from '@openreplay/tracker';

var trackerInstance = (function () {
  // const tracker = new Tracker({
  //   projectKey: "",
  //   __DISABLE_SECURE_MODE: true
  // });
  var mapId = ''
  var userId = ''

  return {
    start() {
      //tracker.start()
    },
    setUserID(value: string | null) {
      if (!value) return
      userId = value
      console.log('User: ' + value)

      let group = (parseInt(userId) - 1) % 4
      console.log('Group: ' + group)
    },
    setMap(value: string) {
      mapId = value.replace('test', '')
      console.log(Date.now() + ',' + userId + ',' + mapId + ',map_loaded')
    },
    setMeta(meta: string, value: any) {
      console.log(Date.now() + ',' + userId + ',' + mapId + ',' + meta + ',' + value)
    },
    push(type: string, payload: any) {
      //tracker.event(type, payload)
      console.log(Date.now() + ',' + userId + ',' + mapId + ',' + type + ',' + payload)
    }
  }
})()

export default trackerInstance
