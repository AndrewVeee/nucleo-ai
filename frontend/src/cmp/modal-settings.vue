<script>

export default {
  props: ['app', 'opts'],
  components: {},
  data() {
    return {
    };
  },  
  methods: {
    onSave: function() {
      this.opts.onSave();
      this.$emit('close');
    },
  },
}
</script>

<template>
<div class="p-2" style="">

  <div class="flex-y mb-2">
    <h4 class="mt-0 mb-1">API Base URL:</h4>
    <input class="form-control flex-grow"
        placeholder="Should be /"
        v-model="app.api.api_base" />
  </div>
  <div class="flex-y mb-2">
    <h4 class="mt-0 mb-1">API Key:</h4>
    <input type="password" class="form-control flex-grow"
        v-model="app.api.api_key" />
  </div>
   <div class="flex-x">
    <div class="flex-grow"></div>
    <button @click="$emit('close')" class="btn mr-3">Cancel</button>
    <button @click="onSave" class="btn btn-pri">Save</button>
  </div>
</div>
</template>
