module.exports = {
    "env": {
        "browser": true,
        "es6": true
    },
    "extends": [
      'plugin:vue/essential',
      'eslint:recommended'
    ],
    "parserOptions": {
        "ecmaVersion": 2018,
        "sourceType": "module",
        "parser": 'babel-eslint'
    },
    "rules": {
        "indent": ["error", 2],
        "vue/html-indent": ["error", 2],
        //"vue/script-indent": ["error", 2],
        "no-console": [
            "error",
            { allow: ["warn", "error"] }
        ],
        "quotes": [
            "error",
            "single",
            { "avoidEscape": true }
        ],
        "no-trailing-spaces": "error",
        "no-multi-spaces": "error",
        "no-unused-vars": "warn",
        "no-unused-expressions": "warn",
        "no-unreachable": "warn",
        "semi-spacing": ["error", {"before": false, "after": true}],
        "semi": [
            "error",
            "always"
        ],
        "comma-dangle": [
            "error",
            "always-multiline"
        ],
    }
};
