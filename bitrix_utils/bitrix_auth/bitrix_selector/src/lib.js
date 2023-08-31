import Vue from 'vue';
import Vuex from 'vuex';
import VueI18n from 'vue-i18n';

import { POPUP_ID, MODE } from './const';
import { store } from './store';
import { messages } from './i18n';
import Selector from './selector.vue';

Vue.use(Vuex);
try { Vue.use(VueI18n); } catch (e) {
  console.warn('VueI18n already initialized');
}

export let t = message => {
  console.warn('App not initialized');
  return message;
};

let _onClose = () => {};

const createApp = ({
  mode,
  callback,
  el = null,
  entities = null,
  multiple = false,
  allowEmpty = false,
  locale = 'ru',
  initiallySelected,
  filter = (() => true),
  style = {},
  excludeBoxChatbots = false,
}) => {
  if (el === null) {
    el = document.createElement('div');
    el.id = POPUP_ID;
    document.body.appendChild(el);
  }
  const i18n = new VueI18n({
    locale: locale.toLowerCase(),
    messages,
  });
  t = i18n.t.bind(i18n);
  return new Vue({
    el: `#${ POPUP_ID }`,
    store: store({
      mode,
      selectCallback: callback,
      entities,
      multiple,
      allowEmpty,
      initiallySelected,
      filter,
      style,
      excludeBoxChatbots,
    }),
    i18n,
    components: { Selector },
    render: h => h(Selector),
  });
};

export const openSelector = ({
  mode,
  entities = null,
  callback = () => null,
  multiple = false,
  allowEmpty = false,
  initiallySelected = null,
  filter = (() => true),
  onClose = (() => {}),
  locale = 'ru',
  style = {},
  excludeBoxChatbots = false,
}) => {
  if (Object.values(MODE).indexOf(mode) === -1) {
    throw new Error(`invalid mode: ${mode}`);
  }
  if (excludeBoxChatbots && mode !== MODE.USER) {
    throw new Error(
      `invalid mode for excludeBoxChatbots: should be ${MODE.USER}, got ${mode}`
    );
  }
  _onClose = onClose;
  if (!initiallySelected) {
    initiallySelected = [];
  } else if (
    typeof initiallySelected === 'string'
    || typeof initiallySelected.length === 'undefined'
  ) {
    initiallySelected = [Number(initiallySelected)];
  } else {
    initiallySelected = initiallySelected.map(Number);
  }
  createApp({
    mode, entities, callback, multiple,
    allowEmpty, initiallySelected, filter, locale,
    style, excludeBoxChatbots,
  });
};

export const closeSelector = () => {
  const el = document.getElementById(POPUP_ID);
  if (el !== null) {
    el.parentElement.removeChild(el);
    _onClose();
  }
};

export default {
  openSelector,
  closeSelector,
};
