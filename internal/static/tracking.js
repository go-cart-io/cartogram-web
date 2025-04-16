/**
 * HTTP contains some helper methods for making AJAX requests
 */
class TrackingHTTP {
  /**
   * Performs an HTTP POST request and returns a promise with the JSON value of the response
   * @param {string} url The URL of the POST request
   * @param {any} form_data The body or form data of the POST request
   * @param {Object} headers The headers of the POST request
   * @param {number} timeout The timeout, in seconds, of the GET request
   * @returns {Promise<Object|string>} A promise to the HTTP response
   */
  static post(url, form_data, headers = {}, timeout = 15000) {
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

      xhttp.ontimeout = function (e) {
        reject(Error("The request has timed out."));
      };

      xhttp.open("POST", url, true);
      xhttp.timeout = timeout;

      Object.keys(headers).forEach(function (key, index) {
        xhttp.setRequestHeader(key, headers[key]);
      });

      xhttp.send(form_data);
    });
  }
}

class TrackingDynamicLoading {
  /**
   * Loads a script and performs an action upon load
   * @param url The URL of the script
   * @param implementationCode The function to be run after loading
   * @param location The element to assign the script tag to
   */
  static loadScript(url, implementationCode, location) {
    let scriptTag = document.createElement("script");
    scriptTag.src = url;

    scriptTag.onload = implementationCode;
    scriptTag.onreadystatechange = implementationCode;

    location.appendChild(scriptTag);
  }
}

class Tracking {
  /**
   * Load the Google Analytics tracking script
   * @param tracking_id The GA tracking ID
   */
  static beginTracking(tracking_id) {
    TrackingDynamicLoading.loadScript(
      "https://www.googletagmanager.com/gtag/js?id=" + tracking_id,
      () => {
        window.dataLayer = window.dataLayer || [];
        window.gtag = function () {
          window.dataLayer.push(arguments);
        };
        window.gtag("js", new Date());
        window.gtag("config", tracking_id);
      },
      document.head
    );
  }

  static consentToTracking() {
    const form = new FormData();
    form.append("consent", "yes");

    TrackingHTTP.post("/api/v1/consent", form).then(
      (response) => {
        document.getElementById("cookie-consent").style.display = "none";
        Tracking.beginTracking(response.tracking_id);
      },
      (err) => console.log(err)
    );
  }

  static optOutOfTracking() {
    const form = new FormData();
    form.append("consent", "no");

    TrackingHTTP.post("/api/v1/consent", form).then(
      (response) => {
        document.getElementById("cookie-consent").style.display = "none";
      },
      (err) => console.log(err)
    );
  }
}
