class GoCartCaptcha {
  /**
   * Performs an HTTP GET request and returns a promise with the JSON value of the response
   * @param {string} url The URL of the GET request
   * @param {number} timeout The timeout, in seconds, of the GET request
   * @param {function} onprogress A function to be called when the request progress information is updated
   * @returns {Promise} A promise to the HTTP response
   */
  get(url, timeout = null, onprogress = null) {
    return new Promise(function (resolve, reject) {
      var xhttp = new XMLHttpRequest();

      xhttp.onreadystatechange = function () {
        if (this.readyState == 4) {
          if (this.status == 200) {
            try {
              resolve(JSON.parse(this.responseText));
            } catch (e) {
              console.log(e);
              console.log(this.responseText);
              reject(Error("Unable to parse output."));
            }
          } else {
            console.log(url);
            reject(Error("Unable to fetch data from the server."));
          }
        }
      };

      if (onprogress !== null) {
        xhttp.onprogress = onprogress;
      }

      xhttp.ontimeout = function (e) {
        reject(Error("The request has timed out."));
      };

      if (timeout !== null) {
        xhttp.timeout = timeout;
      }

      xhttp.open("GET", url, true);
      xhttp.send();
    });
  }

  constructor() {
    this.selectedUI = "image";
    this.UIs = ["image", "audio"];

    this.onSwitch = {
      image: () => {
        document.getElementById("captcha-audio").currentTime = 0.0;
        document.getElementById("captcha-audio").pause();
      },
      audio: () => {
        document.getElementById("captcha-audio").currentTime = 0.0;
        document.getElementById("captcha-audio").play();
      },
    };

    this.onRegenerate = {
      image: (src) => {
        document.getElementById("captcha-image").src = src;
      },
      audio: (src) => {
        document.getElementById("captcha-audio-source").src = src;
        document.getElementById("captcha-audio").load();
      },
    };

    this.UIs.forEach((ui) => {
      document.getElementById("captcha-button-" + ui).addEventListener(
        "click",
        function (_e) {
          this.switchUI(ui);
        }.bind(this)
      );
    }, this);

    document.getElementById("captcha-regenerate").addEventListener(
      "click",
      function (_e) {
        this.regenerate();
      }.bind(this)
    );
  }

  switchUI(newUI) {
    this.selectedUI = newUI;
    document.getElementById("captcha").value = "";

    this.UIs.forEach((ui) => {
      if (ui === newUI) {
        document.getElementById("captcha-button-" + ui).classList.add("active");
        document.getElementById("captcha-ui-" + ui).style.display = "block";

        this.onSwitch[ui]();
      } else {
        document
          .getElementById("captcha-button-" + ui)
          .classList.remove("active");
        document.getElementById("captcha-ui-" + ui).style.display = "none";
      }
    }, this);
  }

  disableUI() {
    document.getElementById("captcha").disabled = true;
    document.getElementById("captcha-regenerate").disabled = true;

    this.UIs.forEach((ui) => {
      document.getElementById("captcha-button-" + ui).disabled = true;
    }, this);
  }

  enableUI() {
    document.getElementById("captcha").disabled = false;
    document.getElementById("captcha-regenerate").disabled = false;

    this.UIs.forEach((ui) => {
      document.getElementById("captcha-button-" + ui).disabled = false;
    }, this);
  }

  regenerate() {
    this.disableUI();

    this.get("/api/v1/gencaptcha").then(
      function (captchas) {
        document.getElementById("captcha").value = "";

        this.UIs.forEach((ui) => {
          this.onRegenerate[ui](captchas["captcha_" + ui]);
        }, this);

        this.onSwitch[this.selectedUI]();

        this.enableUI();
      }.bind(this),
      (err) => console.log(err)
    );
  }
}
