<script>
import * as Settings from '../lib/meta-settings.js';

export default {
  props: ['app', 'is_new', 'chat'],
  components: {},
  data() {
    let settings = {};
    try {
      settings = JSON.parse(this.chat.metadata);
    } catch {
    }
    return {
      name: this.chat.name || 'Assistant',
      temporary: false,
      settings: Settings.get_settings(settings),
    } 
  },  
  methods: {
    onShowSettings: function() {
      this.show_settings = this.sel_chat;
    },
    onSave: function() {
      this.$emit('save', {name: this.name, temp: this.temporary, opts: this.settings});
    },
  },
  beforeUnmount: function() {
  },
  created: function() {
  },
}
</script>

<template>

<div class="flex-y flex-grow p-2">
  <h4 class="my-0 mb-2">{{ is_new ? 'New Chat' : 'Settings - ' + chat.name }}</h4>

  <div class="mt-2">Name:</div>
  <input class="form-control mb-2" v-model="name" />
  
  <div class="mt-2">System Prompt (Tone):</div>
  <AutoTextarea classes="form-control mb-2 text-sm" v-model="settings.system">
  </AutoTextarea>

  <div class="mt-2">Temperature:</div>
  <input class="form-control mb-2" v-model="settings.temperature" />

  <div class="mt-2">Past Messages Sent: {{ settings.chat_history }}</div>
  <input type="range" class="mb-2" max="20" v-model="settings.chat_history" />

  <div class="my-2" v-if="is_new">
    <label>
    <input type="checkbox" v-model="temporary" /> Throwaway (Unsaved Chat)</label>
  </div>

  <div class="mt-2">
    <button @click="onSave" class="btn btn-pri mr-2">{{ is_new ? 'Start Chatting!' : 'Save' }}</button>
    <button @click="$emit('cancel')" class="btn btn-plain">Cancel</button>
  </div>
</div>
</template>
