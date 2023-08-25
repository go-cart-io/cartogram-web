//import Tracker from '@openreplay/tracker';

var trackerInstance = (function() {
  // const tracker = new Tracker({
  //   projectKey: "",  
  //   __DISABLE_SECURE_MODE: true
  // });

  return {
    start: function () {
      //tracker.start()
    },
    setUserID: function (user: string | null) {
      if (!user) return
      console.log('User: ' + user)
    },
    setMeta: function (meta: string, value: any) {
      console.log(Date.now() + ' - ' + meta + ' - ' + value)
    },
    push: function (type: string, payload: any) {
      //tracker.event(type, payload)
      console.log(Date.now() + ' - ' + type + ' - ' + payload)
    }
  };
})();

export default trackerInstance