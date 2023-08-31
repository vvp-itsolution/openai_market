const path = require('path');
const merge = require('webpack-merge');
const webpackConfig = require('./webpack.config');
const VERSION = require("./package.json").version;

module.exports = merge(webpackConfig, {

    devtool: 'source-map',

    output: {
        path: path.join(__dirname, '../static/bitrix_auth/bitrix_selector/dist'),
        filename: '[name]-' + VERSION + '.js',
        libraryTarget: 'umd',
        library: 'bitrixSelector',
	      umdNamedDefine: true
    },

});
