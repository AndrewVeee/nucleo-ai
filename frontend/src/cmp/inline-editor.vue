<script>
  export default {
    props: ['value', 'editing', 'ctl_class'],
    data: function() {
      return {
        cur_val: this.value,
      };
    },
    watch: {
      editing: function(a,b) {
        this.$nextTick(() => {
          if (this.$refs.editor) this.$refs.editor.focus();
        });
      },
    },
    methods: {
      onSave: function() {
        this.$emit('save', this.cur_val);
        this.$emit('cancel');
      }
    },
    created: function() {
    },
    mounted: function() {
      //this.getValue();
    },
  };
</script>
<template>
<div class="flex-x" style="">
  <div v-if="!editing" class="clickable flex-grow"
      @click="$emit('edit')">
    {{ value }}
  </div>
  <input class="flex-grow" :class="ctl_class" v-model="cur_val"
      ref="editor"
      @keypress.enter="onSave"
      @keydown.esc="$emit('cancel')"
      v-if="editing" />
</div>
</template>
