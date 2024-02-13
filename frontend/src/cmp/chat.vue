<script>
import {StreamResponse} from '../lib/api.js';
import ChatSettings from './chat-settings.vue';
import * as Settings from '../lib/meta-settings.js';
import ModalConfirm from './modal-confirm.vue';

export default {
  props: ['app', 'chat_width'],
  components: {ChatSettings},
  data() {
    return {
      messages: [],
      chat_message: '',
      assistant: false,
      multiline: false,
      rag: false,
      sel_chat: null,
      settings: null,
      show_settings: null,
      create_chat: false,
      new_chat_title: '',
      del_message: null,
    } 
  },  
  methods: {
    createMessage: function(role, opts) {
      if (!opts) opts = {}
      return {
        role: role || 'user',
        content: opts.content || '',
        entries: [],
        running: opts.running || false,
        assisntant: false,
        error: null,
        message_id: opts.id || null,
        metadata: opts.metadata,
      }
    },
    saveMessage: function(message) {
      // Don't save message if selected chat doesn't have an id.
      if (!this.sel_chat.id) return;
      this.app.api.send('/store/create', {
        data_type: 'chat_msg',
        parent_type: 'chat',
        parent_id: this.sel_chat.id,
        name: message.role,
        content: message.content,
        metadata: JSON.stringify(message.metadata),
      }).then((r) => {

      });
    },
    onSendMessage: function() {
      //console.log(this.chat_message);
      //console.log("Settings", this.settings);
      let cfg_msg = {role:'config', content:JSON.stringify({
        priority: 10,
        rag: this.rag,
      })};
      let msg = this.createMessage('user', {content: this.chat_message});
      this.saveMessage(msg);
      let prev_messages = this.settings.chat_history;
      let history = [];
      if (prev_messages > 0) history = this.messages.slice(-prev_messages).map((m) => {
          return {role: m.role, content: m.content}
      });
      let messages = [
        cfg_msg,
        ...history,
        ...(this.settings.system ? [{role: 'system', content: this.settings.system}] : []),
        {role: msg.role, content: msg.content},
      ];
      this.messages.push(msg);
      let res = this.createResponse('assistant');
      this.chat_message = '';
      this.sendMessage(messages, res);
      this.scrollChatWin();
    },
    onResponseEvent(response, event) {
      if (event.name == 'content') {
        response.content += event.content;
      } else if (event.name == 'new_entry') {
        this.app.add_entry(event.content);
        response.metadata.events.push(event.content);
      }
      this.scrollChatWin();
    },
    sendMessage: function(messages, response) {
      let model = 'chat';
      if (this.assistant) model = 'assistant';
      let req = this.app.api.completion(messages, model, {temperature: this.settings.temperature || 0.3});
      let res = new StreamResponse(this.onResponseEvent.bind(this, response));
      //response.info = res;
      this.$set(response, 'info', res);
      response.running = true;
      req.run((line) => {
        res.add(line);
      }).catch((err) => {
        response.error = err;
        response.running = false;
      }).finally(() => {
        this.saveMessage(response);
        response.running = false;
      });
    },
    createResponse: function() {
      let response = this.createMessage('assistant', {
        content: '',
        metadata: Settings.get_settings({}, {
          error: null, events: [],
        }),
      });
      this.messages.push(response);
      return response;
    },
    scrollChatWin: function(always) {
      this.$nextTick(() => {
        let chat_win = this.$refs.chat_win;
        if (!chat_win) return;
        //if (!always && chat_win.scrollTop !== (chat_win.scrollHeight - chat_win.offsetHeight)) return;
        chat_win.scrollTo(0,this.$refs.chat_win.scrollHeight);
      });
    },
    onChatEnter: function(evt) {
      if (this.multiline && evt.shiftKey == false) return;
      if (!this.multiline && evt.shiftKey == true) return;
      evt.preventDefault();
      this.onSendMessage();
    },
    onCreateChat: function(evt) {
      if (evt.temp) {
        let chat = {
          id: null,
          name: evt.name,
          metadata: JSON.stringify(evt.opts),
          messages: [],
        };
        this.app.chat_list.unshift(chat);
        this.onSelectChat(chat);
        this.create_chat = false;
        return;
      }
      this.app.api.send('/store/create', {
        data_type: 'chat',
        name: evt.name,
        metadata: JSON.stringify(evt.opts),
      }).then((r) => {
        this.app.chat_list.unshift(r);
        this.new_chat_title = '';
        this.create_chat = false;
        this.onSelectChat(r);
      });
    },
    onSelectChat: function(chat) {
      let md = {};
      try {
        md = JSON.parse(chat.metadata);
      } catch {}
      this.settings = Settings.get_settings(md);
      if (chat.id === null) {
        this.sel_chat = chat;
        this.messages = chat.messages || [];
        this.$nextTick(() => {this.scrollChatWin(true)});
        return;
      }
      this.app.api.send('/store/list', {
        data_type: 'chat_msg',
        parent_type: 'chat',
        parent_id: chat.id,
        order: ['created_at', 'asc'],
      }).then((msgs) => {
        this.messages = msgs.map((msg) => {
          // TODO: Add metadata
          let md = {};
          try { md = JSON.parse(msg.metadata) } catch {}
          let new_msg = this.createMessage(msg.name, {content: msg.content, id: msg.id, metadata: md});
          new_msg.info = {};
          return new_msg;
        });
        this.sel_chat = chat;
        this.$nextTick(() => {this.scrollChatWin(true)});
      });
    },
    onShowSettings: function() {
      this.show_settings = this.sel_chat;
    },
    onSaveSettings: function(evt) {
      this.sel_chat.name = evt.name;
      this.sel_chat.metadata = JSON.stringify(evt.opts);
      this.settings = evt.opts;
      this.show_settings = null;
      if (!this.sel_chat.id) return;
      this.app.api.send('/store/update', {
        id: this.sel_chat.id,
        name: evt.name,
        metadata: this.sel_chat.metadata,
      });
    },
    delete_chat: function(chat, idx) {
      this.app.chat_list.splice(idx, 1);
      if (chat.id === null) return;
      if (chat.id > 0) {
        this.app.api.send('/store/delete_match', {
          parent_type: 'chat',
          parent_id: chat.id,
        }).then((r) => {
          this.app.api.send('/store/delete', {id: chat.id});
        });
      }
    },
    onDelChat: function(chat, idx) {
      this.app.open_modal({
        cmp: ModalConfirm,
        title: 'Delete Chat: ' + chat.name,
        message: 'Are you sure you want to delete this chat and all messages?',
        onConfirm: () => {
          this.delete_chat(chat, idx);
        },
      });
    },
    onDeleteMessage: function(msg, idx) {
      this.del_message = null;
      this.messages.splice(idx, 1);
      if (msg.message_id) {
        this.app.api.send('/store/delete', {id: msg.message_id});
        //console.log("Del", msg.message_id);
      }
    },
  },
  beforeUnmount: function() {
  },
  created: function() {
  },
}
</script>

<template>
<div key="settings" class="flex-y flex-grow flex-stretch" v-show="chat_width > 15">
  <div style="align-items: center; width: auto; overflow: hidden;" class="flex-y flex-grow shadow"
      v-if="show_settings || !sel_chat">
    <ChatSettings :app="app" :chat="show_settings" v-if="show_settings"
        @cancel="show_settings = null"
        @save="onSaveSettings"
        style="max-width: 1000px; width: 99%;" 
        class="flex-y flex-grow p-2">
    </ChatSettings>
    <div key="create_chat" v-else-if="!sel_chat" class="flex-y flex-grow p-2"
        style="max-width: 1000px; width: 99%;">
      <ChatSettings class="flex-y flex-stretch" v-if="app.chat_list.length == 0 || create_chat"
          :app="app" :is_new="true" :chat="{name: new_chat_title, metadata: ''}"
          @cancel="create_chat = false"
          @save="onCreateChat"
          >
      </ChatSettings>
      <div v-else class="flex-grow" style="overflow-y: auto;">
        <div class="flex-x mb-3">
          <h4 class="mt-0 mb-0">Select Chat</h4>
          <div class="flex-grow"></div>
          <button @click="create_chat=true" class="btn btn-pri">Create New Chat</button>
        </div>
        <div class="flex-x mb-3 pr-1" v-for="chat,idx in app.chat_list">
          <div @click="onSelectChat(chat)" class="flex-grow no-shadow card clickable p-1 px-2">
            <span v-if="chat.id === null" class="text-xs pr-2">[TEMP]</span>
            {{ chat.name }}
          </div>
          <div class="flex-grow" v-if="false"></div>
          <button @click="onDelChat(chat,idx)" class="btn btn-plain">
            <svg-icon name="trash"></svg-icon>
          </button>
        </div>
      </div>
    </div>
  </div>
  
  <div key="chat" class="flex-y flex-grow" style="align-items: center;" v-if="sel_chat" v-show="!show_settings && sel_chat">
    <div style="max-width: 1000px; width: 99%" class="flex-y flex-grow shadow xbg-light"
        v-show="chat_width > 15">
      <div class="mb-1 flex-x">
        <button @click="sel_chat = null" class="btn btn-plain btn-sm">
          <svg-icon name="chevron-left" size="18"></svg-icon>
        </button>
        <h4 class="xcard p-1 mt-0 mb-1">Chat with {{ sel_chat.name }}</h4>
      </div>

      <div class="flex-grow" ref="chat_win" style="overflow-y: scroll; height: 0;">
        <div :key="msg.message_id" v-for="msg,idx in messages" class="p-1 px-2 mb-2 round-xl"
            style="overflow-x: auto;"
            :style="{backgroundColor: msg.role == 'user' ? 'var(--bg-sec)' : 'var(--bg-main)'}">
          <div v-if="del_message === idx">
            <div class="flex-x">
              <span>Are you sure you want to delete this message?</span>
              <div class="flex-grow"></div>
              <button @click="del_message = null" class="btn mr-2">Cancel</button>
              <button @click="onDeleteMessage(msg, idx)" class="btn btn-pri">Delete</button>
            </div>
          </div>
          <div v-if="msg.role == 'user'" style="text-align: right; white-space: pre-wrap;">
            <button @click="del_message = idx" class="btn btn-sm muted ml-2" style="float: right;">
              <svg-icon name="trash" size="14"></svg-icon>
            </button>
            <span style="white-space: pre-wrap">{{ msg.content }}</span>
          </div>
          <div v-else-if="msg.role == 'assistant'">
            <button @click="del_message = idx" class="btn btn-sm muted ml-2" style="float: right;">
              <svg-icon name="trash" size="14"></svg-icon>
            </button>
            <div class="mb-1 text-sm" v-if="msg.content" v-html="app.markdown(msg.content)"></div>
            <div class="mb-1 text-sm" style="white-space: pre-wrap" v-else-if="msg.info">{{ msg.info.response }}</div>
            <div>
              <div :key="entry.id" v-if="entry.data_type != 'stream'" v-for="entry in msg.metadata.events" style="display: inline-block;"
                  @click="app.open_entry(entry)"
                  class="clickable text-sm bg-sec mr-2">
                New {{ entry.data_type }}
              </div>
            </div>
            <div class="mb-1 text-sm text-muted" style="white-space: normal;"
                v-if="msg.info">
              <div class="xbg-sec">
                <div v-if="msg.running">
                  <div class="text-sm">
                    <span :key="idx" v-for="state,idx in msg.info.state" class="pr-1"
                        style="border-right: 1px dashed #aaa">
                      {{ state }}
                    </span>
                  </div>
                  <div class="flex-x text-sm">
                    <div v-if="msg.info.status">Status: {{ msg.info.status  }}</div>
                    <div class="flex-grow"></div>
                  </div>
                </div>
              </div>
            </div>
            <div class="mt-2" v-if="msg.error">
              Error: {{msg.error}}
            </div>
          </div>
          <div v-else>
            {{msg}}
          </div>
        </div>
      </div>
      <div class="xflex-x xp-1">
        <AutoTextarea
            @keypress.enter="onChatEnter"
            classes="form-control p-1 flex-grow text-sm" v-model="chat_message"
            class="flex-grow"
            style="max-height: 200px; overflow:hidden;"
            :buffer="0"
            :styles="{fontFamily: 'unset', maxHeight: '100%'}">
        </AutoTextarea>
        <div class="flex-x text-xs pt-2">
          <div class="clickable xpy-1"
              :class="multiline ? '' : 'muted'"
              @click="multiline = !multiline">
            Multiline: <i>{{ multiline ? 'On': 'Off' }}</i>
          </div>
          <div class="clickable xpy-1 ml-4"
              :class="assistant ? '' : 'muted'"
              @click="assistant = !assistant">
            Assistant: <i>{{ assistant? 'On': 'Off' }}</i>
          </div>
          <div class="clickable xpy-1 ml-4"
              :class="rag ? '' : 'muted'"
              @click="rag = !rag">
            Docs: <i>{{ rag ? 'On' : 'Off' }}</i>
          </div>
          <div class="flex-grow"></div>
          <button @click="onShowSettings" class="btn btn-sm btn-plain">
            <svg-icon name="settings"></svg-icon>
          </button>
        </div>
      </div>
    </div>
  </div>
</div>
</template>
