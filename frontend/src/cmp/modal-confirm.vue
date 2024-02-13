<script>

export default {
  props: ['app', 'opts'],
  components: {},
  data() {
    return {
    };
  },  
  methods: {
    onConfirm: function() {
      this.opts.onConfirm();
      this.$emit('close');
    },
  },
}
</script>

<template>
<div class="p-2" style="">

  <p>{{ opts.message || "Confirm action." }}</p>
  
  <div class="flex-x">
    <div class="flex-grow"></div>
    <button @click="$emit('close')" class="btn mr-3">{{ opts.negative || 'Cancel' }}</button>
    <button @click="onConfirm" class="btn btn-pri">{{ opts.confirm || 'Yes' }}</button>
  </div>
</div>
</template>
