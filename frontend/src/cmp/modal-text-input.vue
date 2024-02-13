<script>

export default {
  props: ['app', 'opts'],
  components: {},
  data() {
    return {
      content: this.opts.content,
      multiline: this.opts.multiline,
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
      this.$refs.content.focus();
    });
  },
  created: function() {
  },
}
</script>

<template>
<div class="p-2 pt-0 flex-grow flex-y" style="">
  <p v-if="opts.info">{{opts.info}}</p>
  <div class="flex-x flex-grow flex-stretch" style="overflow-y: auto;">
    <input @keypress.enter="onSave" type="text" ref="content" v-model="content" class="form-control flex-grow" v-if="!multiline" />
    <textarea v-model="content" ref="content" class="form-control flex-grow" :rows="opts.rows || 10" v-else>
    </textarea>
  </div>

  <div class="mt-2 flex-x">
    <div class="flex-grow"></div>
    <button @click="$emit('close')" class="btn btn-plain">Cancel</button>
    <button @click="onSave" class="btn btn-pri ml-2" v-if="!opts.hide_save">Save</button>
  </div>
</div>
</template>
