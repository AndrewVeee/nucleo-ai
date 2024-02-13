<script>

import {AIChatJob, FindListItems} from '../lib/ai-job.js';
import TodoList from './todo-list.vue';
import DocList from './doc-list.vue';
import PromptList from './prompt-list.vue';
import Stream from './stream.vue';
import Modal from './modal.vue';
import ModalTextInput from './modal-text-input.vue';
import ModalSettings from './modal-settings.vue';
import Chat from './chat.vue';

export default {
  props: ['app'],
  components: {TodoList, DocList, Stream, Modal, Chat},
  data() {
    return {
      todo_list: this.app.todo_list,
      new_todo: '',
      chat_msg: '',
      chat_handler: null, //'User Request',
      logs: this.app.ai_log,
      views: {todo: TodoList, prompts: PromptList},
      view: 'stream',
      AIChatJob: AIChatJob,
      resize: null,
      dark_mode: this.app.load_local('dark', false) == "true",
    };
  },
  methods: {
    toggleDark: function() {
      this.dark_mode = this.app.save_local('dark', !this.dark_mode);
    },
    setAITone: function() {
      this.app.open_modal({title: 'AI Tone',
        cmp: ModalTextInput,
        multiline: false,
        content: this.app.ai_tone,
        info: 'Give your assistant some personality. Write a short sentence to describe how they should reply (even add a name).',
        onSave: (value) => {
          this.app.save_local('ai_tone', value);
          this.app.ai_tone = value;
        },
      });
    },
    onResizeMove: function(evt) {
      let new_perc = (1 - evt.pageX / window.innerWidth) * 100;
      if (new_perc < 0) new_perc = 0;
      else if (new_perc > 80) new_perc = 80;
      this.app.chat_width = new_perc;
    },
    onResizeStart: function(evt) {
      evt.preventDefault();
      this.resize = {
        onmove: this.onResizeMove.bind(this),
        pos: evt.pageX,
      };
      this.resize.onend = (evt) => {
        window.removeEventListener('mousemove', this.resize.onmove);
        window.removeEventListener('mouseup', this.resize.onend);
        this.app.save_local('chat_width', this.app.chat_width);
      }
      window.addEventListener('mousemove', this.resize.onmove);
      window.addEventListener('mouseup', this.resize.onend);
    },
    onOpenSettings: function() {
      this.app.open_modal({title: 'Settings',
        cmp: ModalSettings,
        onSave: () => {
          this.app.save_local('api_base', this.app.api.api_base);
          this.app.save_local('api_key', this.app.api.api_key);
          this.app.check_con().then((r) => {
            this.app.load_data();
          });
        },
      });
    },
    },
  created: function() {
    this.app.check_con().catch((err) => {

    })
  },
}
</script>

<template>
<div class="flex-grow flex-y bg-sec"
    :class="dark_mode ? 'dark' : ''">
  <div class="flex-x m-1 mb-2 mx-2 xcard round-sm">
    <div class="ml-0 card flex-x flex-ctr">
      <h4 class="my-0 mr-3">Nucleo</h4>
      <button @click="view = 'stream'" class="btn btn-sm btn-tab mr-2"
          :class="view == 'stream' ? 'btn-tab-sel' : ''">Stream</button>
      <button @click="view = 'todo'" class="btn btn-sm btn-tab mr-2"
          :class="view == 'todo' ? 'btn-tab-sel' : ''">To Do</button>
      <button @click="view = 'docs'" class="btn btn-sm btn-tab mr-2"
          :class="view == 'docs' ? 'btn-tab-sel' : ''">Docs</button>
      <button @click="view = 'chat'" class="btn btn-sm btn-tab mr-2"
          :class="view == 'chat' ? 'btn-tab-sel' : ''">Chat</button>
    </div>
    <div class="flex-grow"></div>
    <button @click="onOpenSettings" class="btn btn ml-2 flex-x flex-ctr" title="Settings">
      <span v-if="!app.connected && app.connect !== null" class="mr-2">Connection Error!</span>
      <svg-icon name="settings"></svg-icon>
    </button>
    <button @click="toggleDark" class="btn ml-2" :class="dark_mode ? 'btn-pri' : 'btn-plain'">
      <svg-icon name="moon"></svg-icon>
    </button>
  </div>
  <div class="flex-x flex-grow flex-stretch pt-0">
    <!-- Main Section -->
    <div class="flex-x flex-stretch"
        :style="{width: app.mobile ? '100%' : (100-app.chat_width) + '%'}"
        v-show="view != 'chat'">
      <Stream :app="app" v-show="view == 'stream'"></Stream>
      <TodoList :app="app" v-show="view == 'todo'"></TodoList>
      <DocList :app="app" v-show="view == 'docs'"></DocList>
      <!-- Slider -->
      <div class="flex-y" style="padding: 7px; cursor: ew-resize"
          @mousedown="onResizeStart"
          v-if="!app.mobile && view != 'chat'"
      >
        <div class="flex-grow" style="border-left: 1px solid var(--accent-color);"></div>
      </div>
    </div>

    <!-- Sidebar -->
    <div class="flex-y mb-2 mr-1"
        :style="{width: view == 'chat' ? '100%' : app.chat_width + '%'}"
        v-show="view == 'chat' || !app.mobile">
      <chat :app="app"
          :chat_width=" view == 'chat' ? 100 : app.chat_width"
        >
      </chat>
    </div>
  </div>

  <Modal :key="modal.id" :app="app" :cfg="modal" v-for="modal,idx in app.modals"
      v-show="idx==0">
  </Modal>
</div>
</template>
