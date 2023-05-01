////////////////////////////////////////////////////////////////////////////////
// This file is part of df_websockets                                          /
//                                                                             /
// Copyright (C) 2020 Matthieu Gallet <github@19pouces.net>                    /
// All Rights Reserved                                                         /
//                                                                             /
// You may use, distribute and modify this code under the                      /
// terms of the (BSD-like) CeCILL-B license.                                   /
//                                                                             /
// You should have received a copy of the CeCILL-B license with                /
// this file. If not, please visit:                                            /
// https://cecill.info/licences/Licence_CeCILL-B_V1-en.txt (English)           /
// or https://cecill.info/licences/Licence_CeCILL-B_V1-fr.txt (French)         /
//                                                                             /
////////////////////////////////////////////////////////////////////////////////

'use strict';

// noinspection JSUnresolvedFunction
const path = require('path');

// noinspection JSUnresolvedVariable,JSUnresolvedFunction
module.exports = [{
  entry: {
    "df_websockets": ['./df_websockets/app.js', './df_websockets/base.js', './df_websockets/forms.ts'],
  },
  resolve: {
    extensions: ['.ts', '.js', '.json']
  },
  output: {
    path: path.resolve(__dirname, '../'),
    filename: 'df_websockets/static/js/[name].min.js'
  },

  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      }
    ]
  },
  // Useful for debugging.
  devtool: 'source-map',
  performance: {hints: false}
},
  {
    entry: {
      "df_websockets": ['./df_websockets/app.js', './df_websockets/base.js', './df_websockets/forms.ts'],
    },
    resolve: {
      extensions: ['.ts', '.js', '.json']
    },
    output: {
      path: path.resolve(__dirname, './'),
      filename: 'dist/js/[name].min.js'
    },

    module: {
      rules: [
        {
          test: /\.tsx?$/,
          use: 'ts-loader',
          exclude: /node_modules/,
        }
      ]
    },
    // Useful for debugging.
    devtool: 'source-map',
    performance: {hints: false}
  },
  {
    entry: {
      "df_websockets": ['./df_websockets/app.js', './df_websockets/base.js', './df_websockets/forms.ts'],
    },
    resolve: {
      extensions: ['.ts', '.js', '.json']
    },
    output: {
      path: path.resolve(__dirname, './'),
      filename: 'dist/js/[name].js'
    },

    module: {
      rules: [
        {
          test: /\.tsx?$/,
          use: 'ts-loader',
          exclude: /node_modules/,
        }
      ]
    },
    devtool: 'source-map',
    optimization: {
      minimize: false
    },
    performance: {hints: "warning"}
  }];