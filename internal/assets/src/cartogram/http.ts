/**
 * HTTP contains some helper methods for making AJAX requests
 */
export default class HTTP {
  /**
   * Performs an HTTP GET request and returns a promise with the JSON/CSV value of the response
   * @param {string} url The URL of the GET request
   * @param {number} timeout The timeout, in seconds, of the GET request
   * @param {function} onprogress A function to be called when the request progress information is updated
   * @param {boolean} parse_json Whether to parse the response as JSON
   * @returns {Promise} A promise to the HTTP response
   */
  static get(
    url: string,
    timeout: number = null,
    onprogress: any = null,
    parse_json: boolean = true
  ): Promise<Object | string> {
    return new Promise(function (resolve, reject) {
      var xhttp = new XMLHttpRequest()

      xhttp.onreadystatechange = function () {
        if (this.readyState == 4) {
          if (this.status == 200) {
            try {
              if (!parse_json) {
                resolve(this.response)
              } else {
                resolve(JSON.parse(this.responseText))
              }
            } catch (e) {
              console.log(e)
              console.log(this.responseText)
              reject(Error('Unable to parse output.'))
            }
          } else {
            console.log(url)
            reject(Error('Unable to fetch data from the server.'))
          }
        }
      }

      if (onprogress !== null) {
        xhttp.onprogress = onprogress
      }

      xhttp.ontimeout = function (e) {
        reject(Error('The request has timed out.'))
      }

      if (timeout !== null) {
        xhttp.timeout = timeout
      }

      xhttp.open('GET', url, true)
      xhttp.send()
    })
  }

  /**
   * Performs an HTTP POST request and returns a promise with the JSON value of the response
   * @param {string} url The URL of the POST request
   * @param {any} form_data The body or form data of the POST request
   * @param {Object} headers The headers of the POST request
   * @param {number} timeout The timeout, in seconds, of the GET request
   * @returns {Promise<Object|string>} A promise to the HTTP response
   */
  static post(
    url: string,
    form_data: any,
    headers: { [key: string]: any } = {},
    timeout: number = 30000
  ): Promise<Object | string> {
    return new Promise(function (resolve, reject) {
      var xhttp = new XMLHttpRequest()

      xhttp.onreadystatechange = function () {
        if (this.readyState == 4) {
          if (this.status == 200) {
            try {
              resolve(JSON.parse(this.responseText))
            } catch (e) {
              console.log(e)
              console.log(this.responseText)
              reject(Error('Unable to parse output.'))
            }
          } else {
            console.log(url)
            reject(Error('Unable to fetch data from the server.'))
          }
        }
      }

      xhttp.ontimeout = function (e) {
        reject(Error('The request has timed out.'))
      }

      xhttp.open('POST', url, true)
      xhttp.timeout = timeout

      Object.keys(headers).forEach(function (key, index) {
        xhttp.setRequestHeader(key, headers[key])
      })

      xhttp.send(form_data)
    })
  }

  /**
   * serializePostVariables produces a www-form-urlencoded POST body from the given variables.
   * @param {Object.<string,string>} vars The variables to encode in the body
   * @returns {string}
   */
  static serializePostVariables(vars: { [key: string]: string }): string {
    var post_string = ''
    var first_entry = true

    Object.keys(vars).forEach(function (key, index) {
      post_string += (first_entry ? '' : '&') + key + '=' + encodeURIComponent(vars[key])
      first_entry = false
    })

    return post_string
  }

  /**
   * generateMIMEBoundary generates a random string that can be used as a boundary in a multipart MIME post body.
   * @returns {string}
   */
  static generateMIMEBoundary(): string {
    var text = '---------'
    var possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'

    for (var i = 0; i < 25; i++)
      text += possible.charAt(Math.floor(Math.random() * possible.length))

    return text
  }
}
