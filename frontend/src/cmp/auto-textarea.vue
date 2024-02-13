<script>
  export default {
    props: ['value', 'classes', 'styles', 'placeholder', 'buffer'],
    inheritAttrs: false,
    data: function() {
      return {
        buffer_px: this.buffer || 15,
      };
    },
    computed: {
      listeners() {
        const { input, ...listeners } = this.$listeners;
        return listeners;
      },
      rows() {
        return this.$attrs.rows || 1;
      },
      attrs() {
        const { rows, ...attrs } = this.$attrs;
        return attrs;
      },
    },
    methods: {
      input: function(evt) {
        this.$emit('input', event.target.value);
      },
      focus: function() {
        this.$refs.textarea.focus();
      },
      scrollIntoView: function(opts) {
        this.$refs.textarea.scrollIntoView(opts);
      },
    },
    created: function() {
    },
    mounted: function() {
      //this.getValue();
    },
  };
</script>
<template>
<div class="grow-wrap" style="display: grid;">
  <div :class="classes" :style="{paddingBottom: buffer_px + 'px', ...styles}" style="height: auto !important; white-space: pre-wrap; visibility: hidden; grid-area: 1 / 1 / 2 / 2;"
    >{{value}}<br v-if="(value || '').endsWith('\n')" /><span v-else></span></div>
  <textarea ref="textarea" :value="value" :class="classes" :style="styles"
      @input="input" style="overflow: hidden; grid-area: 1 / 1 / 2 / 2"
      :rows="rows"
      :placeholder="placeholder"
      v-on="listeners"
    ></textarea>
</div>
</template>
