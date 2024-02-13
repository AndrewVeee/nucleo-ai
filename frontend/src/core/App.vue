<script>
import Main from './Main.vue'
import {App} from './app.js'

export default {
  props: ['AppInit'],
  components: {Main},
  data() {
    return {
      app: null,
    };
  },
  created() {
    console.log("AppInit", this.AppInit);
    let app = new App(this.AppInit);
    app.ready.then(() => {
      //console.log("App initialized", {...app.tool_cache});
      this.app = app;
    });
    window.app = app;
  },
}
</script>

<template>
  <Main :app="app" v-if="app" />
</template>

