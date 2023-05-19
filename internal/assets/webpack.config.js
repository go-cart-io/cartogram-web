const path = require('path')
const { WebpackManifestPlugin } = require('webpack-manifest-plugin')

module.exports = {
  entry: {
    main: './src/index.js',
    cartogram: './src/cartogram/cartogram.js'
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js']
  },
  module: {
    rules: [
      {
        test: /\.ts?$/,
        use: 'ts-loader',
        exclude: /node_modules/
      }
    ]
  },
  output: {
    filename: '[name].[contenthash].js',
    publicPath: '/static/dist/',
    path: path.resolve(__dirname, '..', 'static', 'dist'),
    clean: true,
    library: { type: 'umd' },
    globalObject: 'this'
  },
  plugins: [new WebpackManifestPlugin()]
}
