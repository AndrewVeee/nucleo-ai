<script>

export default {
  props: ['app', 'opts'],
  components: {},
  data() {
    return {
      content: this.opts.content,
    };
  },  
  methods: {
    onSave: function() {
      this.opts.onSave(this.content);
      this.$emit('close');
    },
  },
  beforeUnmount: function() {
  },
  mounted: function() {
    this.$nextTick(() => {
      //this.$refs.content.focus();
    });
  },
  created: function() {
  },
}
</script>

<template>
<div class="p-2 pt-0 flex-y flex-grow" style="">
  <h2 v-if="false && opts.title">{{opts.title}}</h2>
  <div v-if="opts.source" class="text-sm">
    Source: <a :href="opts.source" target="_blank">{{ opts.source }}</a>
  </div>
  <div class="flex-grow flex-scroll" style="overflow-y: scroll; ">
    <pre v-if="false" style="white-space: pre-wrap">{{ this.content }}</pre>
    <div v-html="app.markdown(this.content)"></div>
  </div>

  <button @click="onSave" class="btn btn-pri mt-2" v-if="false && !opts.hide_save">Save</button>
</div>
</template>
