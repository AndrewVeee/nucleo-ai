import Vue from 'vue';
import './core/style.scss'
import App from './core/App.vue'
import * as AppInit from './app.js'

AppInit.init.vue = Vue;
new Vue({
  render: (h) => h(App, {props: {AppInit: AppInit}}),
}).$mount('#app');
