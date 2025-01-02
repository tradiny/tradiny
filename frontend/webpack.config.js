/*
 * This software is licensed under a dual-license model:
 * 1. Under the Affero General Public License (AGPL) for open-source use.
 * 2. With additional terms tailored to individual users (e.g., traders and investors):
 *
 *    - Individual users may use this software for personal profit (e.g., trading/investing)
 *      without releasing proprietary strategies.
 *
 *    - Redistribution, public tools, or commercial use require compliance with AGPL
 *      or a commercial license. Contact: license@tradiny.com
 *
 * For full details, see the LICENSE.md file in the root directory of this project.
 */

const path = require("path");
const webpack = require("webpack");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");

const isProduction = process.env.NODE_ENV === "production";

const copyPatterns = [
  { from: "LICENSE.md", to: "LICENSE.md" },
  { from: "static/service-worker.js", to: "service-worker.js" },
  {
    from: "node_modules/blueimp-tmpl/js/tmpl.min.js",
    to: "js/blueimp-tmpl.min.js",
  },
  { from: "node_modules/d3/dist/d3.min.js", to: "js/d3.min.js" },
  {
    from: "node_modules/d3fc/packages/d3fc/build/d3fc.min.js",
    to: "js/d3fc.min.js",
  },
  { from: "favicon.ico", to: "favicon.ico" },
];

if (!isProduction) {
  copyPatterns.push({ from: "examples", to: "examples" });
}

module.exports = {
  entry: "./index.js",
  output: {
    filename: "tradiny.js",
    path: path.resolve(__dirname, "dist"),
  },
  module: {
    rules: [
      {
        test: /\.html$/,
        include: path.resolve(__dirname, "templates"),
        use: "raw-loader",
      },
      {
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, "css-loader"],
      },
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
          options: {
            presets: ["@babel/preset-env"],
          },
        },
      },
    ],
  },
  resolve: {
    extensions: [".js", ".html"],
    alias: {},
  },
  plugins: [
    new webpack.BannerPlugin({
      banner:
        "Tradiny -- Copyright (c) 2018-present, Bysoft s. r. o. -- For license information please see LICENSE.md",
    }),
    new CopyWebpackPlugin({
      patterns: copyPatterns,
    }),
    new MiniCssExtractPlugin({
      filename: "tradiny.css",
    }),
    new HtmlWebpackPlugin({
      template: "./index.html",
      filename: "index.html",
      minify: true,
    }),
  ],
  optimization: {
    minimizer: [
      "...", // This adds the existing minimizers (like `terser-webpack-plugin` for JS)
      new CssMinimizerPlugin(),
    ],
  },
  devServer: {
    static: [
      {
        directory: path.join(__dirname, "dist"),
      },
      {
        directory: path.join(__dirname, "node_modules"),
        publicPath: "/node_modules",
      },
    ],
    compress: true,
    // host: "192.168.2.36",
    port: 9000,
    open: {
      target: ["examples/candlestick.html"],
    },
  },
  externals: {
    tmpl: "tmpl",
    d3: "d3",
    d3fc: "fc",
  },
  mode: isProduction ? "production" : "development",
};
