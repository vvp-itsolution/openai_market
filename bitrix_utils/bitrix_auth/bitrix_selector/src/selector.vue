<template>
  <div :id="POPUP_ID" class="popup" :style="style">
    <h3 class="title mb-4">
      <span class="title-text">{{
        multipleSelectionMode
          ? $t(MSG.SELECT_MANY[mode])
          : $t(MSG.SELECT_ONE[mode])
      }}</span>
      <a class="close" @click="resetAndClose()">&times;</a>
    </h3>
    <div v-if="error !== null" class="error-box mb-2">{{ error.message }}</div>
    <div class="flex-row">
      <i v-if="loadingEntities">{{ $t('message.loading') }}</i>
      <vue-select
        v-else
        :value="selectedEntitiesOrEntity"
        :options="sortedEntities"
        :multiple="multipleSelectionMode"
        :label="mode === MODE.USER ? 'fullName' : 'NAME'"
        :class="{'multiple-selection-mode': multipleSelectionMode}"
        class="entity-select"
        @input="onSelectInput"
      >
        <template slot="option" slot-scope="entity">
          <i
            v-if="showExtranetIcon(entity)"
            class="extranet-icon"
            :title="$t(MSG.EXTRANET[mode])"
          />
          {{ mode === MODE.USER ? entity.fullName : entity.NAME }}
        </template>
      </vue-select>
      <!--div>
        Model: {{ selectedEntitiesOrEntity }}
      </div-->
      <div><button
        :title="$t('message.choose')"
        type="button"
        class="apply-btn"
        @click="applySelection()"
      ><svg
        xmlns="http://www.w3.org/2000/svg"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        version="1.1"
        viewBox="0 0 224 224"
        width="24px"
        height="24px"
      ><g
        fill="none"
        fill-rule="nonzero"
        stroke="none"
        stroke-width="1"
        stroke-linecap="butt"
        stroke-linejoin="miter"
        stroke-miterlimit="10"
        stroke-dasharray=""
        stroke-dashoffset="0"
        font-family="none"
        font-weight="none"
        font-size="none"
        text-anchor="none"
        style="mix-blend-mode: normal"
      ><path
        d="M0,224v-224h224v224z"
        fill="none"
      /><g fill="#ffffff"><g id="surface1"><path
        d="M179.95833,49.29167l-95.95833,95.95833l-39.95833,-39.95833l-13.41667,13.41667l46.66667,46.66667l6.70833,6.41667l6.70833,-6.41667l102.66667,-102.66667z"
      /></g></g></g></svg></button></div>
    </div>
  </div>
</template>

<script>
import { mapState, mapGetters, mapMutations, mapActions } from 'vuex';
import { VueSelect } from 'vue-select';

import { POPUP_ID, MSG, MODE } from './const';

export default {
  components: {
    VueSelect,
  },
  created() {
    this.getEntities();
  },
  computed: {
    POPUP_ID: () => POPUP_ID,
    MSG: () => MSG,
    MODE: () => MODE,
    ...mapState([
      'loadingEntities',
      'mode',
      'multipleSelectionMode',
      'style',
      'error',
    ]),
    ...mapGetters([
      'sortedEntities',
      'selectedEntities',
      'selectedEntitiesOrEntity',
    ]),
  },
  methods: {
    onSelectInput(model) {
      this.setSelection({ model });
    },
    ...mapMutations([
      'setSelection',
    ]),
    ...mapActions([
      'getEntities',
      'applySelection',
      'resetAndClose',
    ]),
    isExtranetUser(user) {
      if (this.mode !== MODE.USER) { throw new Error('not a user mode!'); }
      if (!user.UF_DEPARTMENT) { return true; }
      if (user.UF_DEPARTMENT.length === 0) { return true; }
      if (user.UF_DEPARTMENT.length === 1) {
        const departmentId = user.UF_DEPARTMENT[0];
        return departmentId === 0 || departmentId === '0';
      }
      return false;
    },
    isExtranetGroup(group) {
      if (this.mode !== MODE.GROUP) { throw new Error('not a group mode!'); }
      // у групп нет поля IS_EXTRANET если в настройках портала
      // выключен сервис Экстранет, считаем такие группы интранетом
      return (group.IS_EXTRANET || 'N') === 'Y';
    },
    showExtranetIcon(entity) {
      if (this.mode === MODE.USER) {
        return this.isExtranetUser(entity);
      } else if (this.mode === MODE.GROUP) {
        return this.isExtranetGroup(entity);
      }
      return false;
    },
  },
};
</script>

<style lang="scss" scoped>
  .popup {
    position: absolute;
    top: 10%;
    left: 10%;
    width: 80%;
    height: 500px;
    background: #fff;
    border: 1px solid #777;
    padding: 0 1rem 1rem;
    box-shadow: 5px 5px 5px 0 rgba(0,0,0,0.25);
    border-radius: .25rem;
    @media (max-width: 800px) {
      width: 100%;
      left: 0;
    }
  }
  .title {
    display: flex;
    font-size: 24px;
    padding: 1rem;
    margin: 0 -1rem 1.5rem;
    @media (max-width: 800px) {
      font-size: 18px;
      box-shadow: 0 3px 3px 0 rgba(0,0,0,0.25);
    }
    & > .title-text {
      flex: 1;
    }
    & > .close {
      cursor: pointer;
      font-size: 26px;
    }
  }
  .mb-2 {
    margin-bottom: .5rem!important;
  }
  .mb-4 {
    margin-bottom: 1.5rem!important;
  }
  li {
    list-style: none;
  }
  .flex-row {
    display: flex;
    align-items: center;
    .v-select { flex: 1; }
  }
  .popup /deep/ .dropdown-menu {
    overflow-x: hidden;
    li, li > a {
      overflow-x: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    }
  }
  .popup /deep/ .dropdown-toggle {
    border: 0;
    border-radius: 0;
    box-shadow: 0 0 2px 2px rgba(0,0,0,0.25);
    padding-right: 15px;
    &:hover {
      box-shadow: 0 0 3px 3px rgba(0,0,0,0.25);
    }
    &:active, &:focus {
      box-shadow: 0 0 4px 4px rgba(0,0,0,0.25);
    }
    &::after {
      border-color: transparent;
    }
    .input {
      border: 0;
    }
  }
  .error-box {
    background: #daa;
    border: 1px solid #a66;
    padding: 1rem;
    border-radius: .25rem;
  }
  .apply-btn {
    width: 100%;
    padding: 0.5rem;
    margin-left: 10px;
    text-align: center;
    font-weight: 400;
    white-space: nowrap;
    vertical-align: middle;
    user-select: none;
    border: 1px solid transparent;
    padding: .75rem 1rem;
    font-size: 1rem;
    line-height: 1.5;
    color: #fff;
    background-color: #28a745;
    border-color: #28a745;
    cursor: pointer;
    &:focus {
      box-shadow: 0 0 0 0.2rem rgba(40,167,69,.5);
    }
    &:hover {
      background-color: #218838;
      border-color: #1e7e34;
    }
    &:active {
      background-color: #1e7e34;
      border-color: #1c7430;
    }
  }
</style>
<style lang="scss">
  // доработка верстки vue-select
  .entity-select {
    width: 70%;
    &:not(.multiple-selection-mode) .vs__selected-options {
      overflow: hidden;
      flex-wrap: nowrap;
    }
    .form-control, .selected-tag {
       padding: .75rem .75rem !important;
    }
  }
  .v-select.open .open-indicator:before {
    margin-top: 3px;
    margin-bottom: 0;
  }
  .v-select .open-indicator:before {
    margin-bottom: 4px;
  }
</style>

<style lang="scss" scoped>
  .extranet-icon {
    background: url(./assets/icons/extranet.svg);
    display: inline-block;
    vertical-align: text-bottom;
    width: 20px;
    height: 20px;
    margin-right: 8px;
  }
</style>
