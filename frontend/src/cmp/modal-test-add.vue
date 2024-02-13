<script>
import StreamData from '../data/stream.js';

export default {
  props: ['app', 'opts'],
  components: {},
  data() {
    return {
      cont_type: 'email',
      content: '',
      examples: StreamData,
    };
  },  
  methods: {
    onAdd: function() {
      this.opts.onAdd({type: this.cont_type, content: this.content, subject: '', summary: '',
        to: '', from: '', suggestions: [], is_new: true, processed: false});
    },
    selectRandom: function() {
      this.selectEx(this.examples[parseInt(Math.random() * this.examples.length)]);
    },
    selectEx: function(ex) {
      this.cont_type = ex.type;
      this.content = ex.content;
    },
  },
  beforeUnmount: function() {
  },
  created: function() {
  },
}
</script>

<template>
<div class="p-2" style="">

  <div>
    <div>
      Examples:
      <button @click="selectRandom" class="btn ml-2 btn-sm">Random</button>
    </div>

    <div class="clickable m-1" style="display: inline-block"
        @click="selectEx(ex)"
        v-for="ex in examples">
      {{ex.title}}
    </div>
  </div>

  <div class="flex-x mb-2">
    <div class="mr-2">Type:</div>
    <input class="form-control flex-grow" v-model="cont_type" />
  </div>
  <div class="flex-x">
    <div class="mr-2">Content:</div>
  </div>
  <div class="flex-x">
    <textarea v-model="content" class="form-control flex-grow" rows="8"></textarea>
  </div>

  <button @click="onAdd" class="btn btn-pri mt-2">Add</button>
</div>
</template>
