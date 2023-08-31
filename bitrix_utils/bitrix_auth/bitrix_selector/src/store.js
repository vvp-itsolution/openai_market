import Vue from 'vue';
import { Store } from 'vuex';

import { closeSelector, t } from './lib';
import { MODE, BX24_URLS, MSG } from './const';


const state = ({
  mode,
  multipleSelectionMode,
  allowEmpty,
  style,
  excludeBoxChatbots,
}) => ({
  mode,
  entities: {}, // users, groups or departments
  selectedIds: [],
  multipleSelectionMode,
  allowEmpty,
  style: { ...style },
  error: null,
  loadingEntities: true,
  excludeBoxChatbots,
  boxBotIds: null,
});
const getters = (filter) => ({
  sortedEntities: state => {
    // Отфильтровка чатботов
    const {
      excludeBoxChatbots,
      boxBotIds,
      entities,
      mode,
    } = state;
    const botsFilter = excludeBoxChatbots && boxBotIds !== null
      ? (user => !boxBotIds.includes(Number(user.ID)))
      : (() => true);
    return Object.values(entities)
      .filter(filter)
      .filter(botsFilter)
      .sort(sortCompareFn(mode));
  },
  selectedEntities: state =>
    state.selectedIds.map(id => state.entities[id]),
  selectedEntitiesOrEntity: state =>
    selectedEntitiesOrEntity(state),
});

const selectedEntitiesOrEntity =
  ({ entities, selectedIds, multipleSelectionMode }) =>
    multipleSelectionMode
      ? [ ...selectedIds.map(id => entities[id]) ]
      : selectedIds.length === 1
        ? { ...entities[selectedIds[0]] }
        : null;

const isEmptySelection = ({ selectedIds }) =>
  selectedIds.length === 0;

const arrEq = (a1, a2) => {
  if (a1.length !== a2.length) { return false; }
  return a1.every((item, ix) => item === a2[ix]);
};
const sortCompareFn = mode => (entityA, entityB) => {
  const key = mode === MODE.USER ? 'fullName' : 'NAME';
  const valueA = entityA[key];
  const valueB = entityB[key];
  if (valueA < valueB) { return -1; }
  if (valueA > valueB) { return 1; }
  return 0;
};

const mutations = {
  setLoadingEntities: (state, { loadingEntities }) => {
    state.loadingEntities = !!loadingEntities;
  },
  setSelection: (state, { model }) => {
    // model - список объектов или 1 объект в зав-и от state.multipleSelectionMode
    // единственное необходимое поле объекта: ID (int or int-like)
    const selection = state.selectedIds;
    if (state.multipleSelectionMode) {
      const newSelection = model.map(e => Number(e.ID));
      // condition to prevent watchers from endless cycle
      if (!arrEq(selection, newSelection)) {
        state.selectedIds = newSelection;
      }
    } else {
      if (model === null) {
        // condition to prevent watchers from endless cycle
        if (selection.length !== 0) { state.selectedIds = []; }
      } else {
        const ID = Number(model.ID);
        // condition to prevent watchers from endless cycle
        if (selection.length === 1 && selection[0] === ID) { return; }
        state.selectedIds = [ ID ];
      }
    }
    state.error = null;
  },
  setModelFromArray(state, { ids }) {
    this.commit('setSelection', {
      model: state.multipleSelectionMode
        ? ids
          .filter(id => state.entities.hasOwnProperty(id))
          .map(id => ({ID: id}))
        : ids.length !== 0
          ? {ID: ids[0]}
          : null,
    });
  },
  addEntities: (state, entities) => {
    Vue.set(state, 'entities', entities.reduce((map, entity) => {
      entity = { ...entity };
      if (state.mode === MODE.USER) {
        const user = entity;
        let fullName = `${user.NAME || ''} ${user.LAST_NAME || ''}`.trim();
        if (user.EMAIL) {
          fullName = fullName ? `${fullName} (${user.EMAIL})` : user.EMAIL;
        }
        user.fullName = fullName;
      }
      map[entity.ID] = entity;
      return map;
    }, { ...state.entities }));
  },
  onError: (state, { message, error = null }) => {
    state.error = { message, error };
  },
  setBoxBotIds: (state, { boxBotIds }) => {
    if (boxBotIds === null) {
      state.boxBotIds = null;
      return;
    }
    state.boxBotIds = boxBotIds
      .map(Number)
      .filter(id => !Number.isNaN(id));
  },
};

const actions = ({ customEntities, selectCallback, initiallySelected }) => ({
  getEntities: ({ state: { mode, excludeBoxChatbots }, commit, dispatch }) => {
    // Получение пользователей/групп/отделов
    let resolveHandle = null;
    let rejectHandle = null;
    // Мутация и resolve при успешном получении
    const onSuccess = entities => {
      commit('setLoadingEntities', { loadingEntities: false });
      commit('addEntities', entities);
      if (initiallySelected.length) {
        commit('setModelFromArray', { ids: initiallySelected });
      }
      resolveHandle();
    };
    // Мутация и reject при ошибке
    const onError = ({ error, message = null }) => {
      const defaultErr = () => {
        const msgKind = (
          error &&
          error.status === 401 &&
          error.ex &&
          error.ex.error === 'insufficient_scope'
        ) ? MSG.PERMISSION_ERROR : MSG.GET_LIST_ERROR;
        return t(msgKind[mode]);
      };
      commit('setLoadingEntities', { loadingEntities: false });
      commit('onError', {
        error,
        message: message || defaultErr(),
      });
      rejectHandle();
    };

    let fetchEntities;

    commit('setLoadingEntities', { loadingEntities: true });
    if (customEntities !== null) {
      // Инициализация с entities: пользовательские записи или Promise
      fetchEntities = () => Promise.resolve(customEntities)
        .then(entities => onSuccess(entities))
        .catch(error => {
          const message = error && error.message
            ? error.message
            : null;
          onError({ error, message });
        });
    } else {
      // Получение записей через BX24
      const entities = [];
      const bxReq = BX24_URLS[mode];
      fetchEntities = () =>
        window.BX24.callMethod(bxReq.url, bxReq.params, result => {
          let error;
          // eslint-disable-next-line no-cond-assign
          if (error = result.error()) {
            onError({ error });
          } else {
            entities.push(...result.data());
            if (result.more()) {
              result.next();
            } else {
              onSuccess(entities);
            }
          }
        });
    }

    const maybeExcludeChatbots = excludeBoxChatbots
      ? dispatch('getBoxBotIds')
      : Promise.resolve();
    return maybeExcludeChatbots
      .catch(error => {
        onError({ error });
        throw error;
      })
      .then(() => {
        fetchEntities();
        return new Promise((resolve, reject) => {
          resolveHandle = () => resolve();
          rejectHandle = () => reject();
        });
      });
  },
  applySelection: ({ state, commit }) => {
    if (!state.allowEmpty && isEmptySelection(state)) {
      commit('onError', { message: t(MSG.SELECT_ONE[state.mode]) });
      return;
    }
    closeSelector();
    selectCallback(selectedEntitiesOrEntity(state));
  },
  resetAndClose: ({ state, commit }) => {
    commit('setSelection', {
      model: state.multipleSelectionMode ? [] : null,
    });
    closeSelector();
  },
  getBoxBotIds: ({ state, commit }) => {
    if (!state.excludeBoxChatbots) {
      throw new Error('excludeBoxChatbots is false');
    }
    if (state.mode !== MODE.USER) {
      throw new Error('only for user mode');
    }
    if (state.boxBotIds !== null) {
      return Promise.resolve();
    }
    const boxBotIds = [];
    return new Promise((resolve, reject) =>
      window.BX24.callMethod('app.info', null, res => {
        if (res.error()) { return reject(res.error()); }
        if (res.data().LICENSE.indexOf('selfhosted') === -1) {
          // не коробка
          return resolve(false);
        }
        return resolve(true);
      }))
      .then(isBox => isBox
        // коробка - получаем список чатботов
        ? new Promise((resolve, reject) =>
          window.BX24.callMethod('imbot.bot.list', null, res => {
            if (res.error()) { return reject(res.error()); }
            boxBotIds.push(
              ...Object.values(res.data()).map(bot => bot.ID),
            );
            if (!res.more()) { return resolve(boxBotIds); }
          }))
        // облако - не требуется
        : Promise.resolve(null))
      .then(boxBotIds => commit('setBoxBotIds', { boxBotIds }));
  },
});


export const store = ({
  mode,
  selectCallback,
  entities,
  multiple: multipleSelectionMode,
  allowEmpty,
  initiallySelected,
  filter,
  style,
  excludeBoxChatbots,
}) => {
  const store = new Store({
    state: state({ mode, multipleSelectionMode, allowEmpty, style, excludeBoxChatbots }),
    getters: getters(filter),
    mutations,
    actions: actions({
      selectCallback,
      initiallySelected,
      customEntities: entities,
    }),
  });

  /* eslint-disable */
  if (process.env.NODE_ENV === 'development') {
    store.subscribe((mutation) => {
      console.log('bitrix_selector vuex mutation', mutation.type, mutation.payload);
    });
  }
  /* eslint-enable */

  return store;
};
