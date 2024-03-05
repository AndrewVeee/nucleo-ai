<script>
//import StreamEntry from './stream-entry.vue';
import ModalConfirm from './modal-confirm.vue';
import entry_chat from './stream-entry-chat.vue';
import entry_assistant from './stream-entry-assistant.vue';
import entry_research from './stream-entry-research.vue';
import entry_log from './stream-entry-log.vue';
import entry_message from './stream-entry-message.vue';

export default {
  props: ['app', 'item', 'level'],
  components: {entry_chat, entry_log, entry_assistant, entry_message,
      entry_research},
  data() {
    return {
      feed: this.app.feed,
      prompt_test: '',
      new_todo: '',
    } 
  },  
  methods: {
   onAddCont: function() {
      this.app.open_modal({
        title: 'Add Content to Stream',
        cmp: ModalTestAdd,
        onAdd: (res) => {
          this.addContent({type: res.type, content: res.content});
        },
      });
    },
    performDelete: function(entry, idx) {
      this.app.api.send('/store/delete', {id: entry.id}).then((r) => {
        this.app.stream_list.splice(idx, 1);
      });
    },
    onDelete: function(entry, idx, evt) {
      if (evt && evt.skip_confirm) {
        this.performDelete(entry, idx);
        return;
      }
      this.app.open_modal({
        title: 'Delete Entry?',
        cmp: ModalConfirm,
        message: "Are you sure you want to delete this stream entry?",
        onConfirm: () => { this.performDelete(entry, idx) },
      });
    },
    onCreate: function(stream_type) {
      this.app.api.send('/store/create', {
        data_type: 'stream',
        subtype: stream_type,
      }).then((r) => {
        this.app.stream_list.unshift(r);
      });
    }
  },
  beforeUnmount: function() {
  },
  created: function() {
  },
}
</script>

<template>
<div class="ml-2 mb-1 flex-x flex-grow flex-stretch pt-0">
  <div class="flex-grow flex-y" style="overflow-y: auto;">
    <div class="mb-1 flex-x" v-if="false">
      <div style="overflow-x: auto;">
        <div class="card p-1 round-sm text-sm mr-2" style="display: inline-block; max-width: 200px;">
          Important Bill
        </div>
        <div class="card p-1 round-sm text-sm mr-2" style="display: inline-block; max-width: 200px;">
          To Do: Blah
        </div>
      </div>
    </div>
    <div class="shadow text-center mt-2 xflex-x flex-center">
      <div class="text-sm mb-1" style="display: inline-block; font-weight: 300;">Add to your stream...</div>
      <button @click="onCreate('assistant')" class="btn btn-plain ml-3">Assistant Task</button>
      <button @click="onCreate('chat')" class="btn btn-plain ml-3">Quick Chat</button>
      <button @click="onCreate('research')" class="btn btn-plain ml-3">Research</button>
      <button @click="onCreate('message')" class="btn btn-plain ml-3">Message</button>
    </div>
    <div class="flex-scroll-y pr-1 mt-0 ml-2 pr-3">

      <component :key="entry.id" :is="'entry_' + entry.subtype" :app="app" :entry="entry"
          v-for="entry,idx in app.stream_list"
          @delete="onDelete(entry, idx, $event)">
      </component>

    </div>
  </div>
</div>
</template>
