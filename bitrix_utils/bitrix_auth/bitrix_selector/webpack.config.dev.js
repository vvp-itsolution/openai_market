const path = require('path');
const merge = require('webpack-merge');
const webpackConfig = require('./webpack.config');

module.exports = merge(webpackConfig, {

    devtool: 'inline-source-map',

    output: {
        path: path.join(__dirname, '../static/bitrix_auth/bitrix_selector/dev'),
        filename: '[name].js',
        libraryTarget: 'umd',
        library: 'bitrixSelector',
	      umdNamedDefine: true
    },

});
