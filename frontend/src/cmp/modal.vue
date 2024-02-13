<script>

export default {
  props: ['app', 'cfg'],
  components: {},
  data() {
    return {
      header: true,
    } 
  },  
  methods: {
  },
  beforeUnmount: function() {
  },
  created: function() {
  },
}
</script>

<template>
<div @click="app.modals.splice(0,1)" style="position: absolute; left: 0; top: 0; right: 0; bottom: 0; background-color: #0004;">
  <div @click.stop class="card flex-y flex-grow"
      style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 600px;
        max-width: 90%;"
      :style="cfg.opts.style">
    <div class="flex-x xbg-sec round-lg mt-1 mb-3 pb-2">
      <h3 class="my-0" v-if="cfg.opts.title">{{cfg.opts.title}}</h3>
      <div class="flex-grow"></div>
      <button @click="app.close_modal()" class="btn btn-plain">
        <svg-icon name="x"></svg-icon>
      </button>
    </div>
    <component :is="cfg.opts.cmp" :app="app" :opts="cfg.opts" v-bind="cfg.opts.bind" v-if="cfg.opts.cmp"
        class="flex-y flex-grow flex-scroll-y"
        style="height: auto;"
        @hide-header="header = false"
        @close="app.close_modal()"
      >
    </component>
  </div>
</div>
</template>
