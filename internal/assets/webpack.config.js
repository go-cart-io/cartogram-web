const path = require('path');
const { WebpackManifestPlugin } = require('webpack-manifest-plugin')

module.exports = {
  entry: {
    main: './src/index.js',
    cartogram: './src/cartogram/cartogram.js',
  },
  output: {
    filename: '[name].[contenthash].js',
    publicPath: '/static/dist/',
    path: path.resolve(__dirname, '..', 'static', 'dist'),
    clean: true,
    library: { type: 'umd' },
    // prevent error: `Uncaught ReferenceError: self is not define`
    globalObject: 'this'
  },
  plugins: [
    new WebpackManifestPlugin()
  ]
};