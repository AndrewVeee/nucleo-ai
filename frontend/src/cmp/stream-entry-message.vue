<script>
import {StreamResponse} from '../lib/api.js';
import ModalDoc from './modal-doc.vue';
import * as Settings from '../lib/meta-settings.js';

export default {
  props: ['app', 'entry'],
  data() {
    if (!this.entry.name) this.entry.name = '';
    if (!this.entry.content) this.entry.content = '';
    return {
      metadata: {},
      is_new: this.entry.name ? false : true,
      running: false,
    } 
  },  
  methods: {
    onInitialSave: function() {
      this.app.api.send('/store/update', {
        id: this.entry.id, name: this.entry.name,
      }).then((r) => {
        this.is_new = false;
      });
      this.sendMessage();
    },
    onResponseEvent: function(event) {
      if (event.name == 'content') {
        this.entry.content += event.content;
      } else if (event.name == 'category') {
        this.metadata.category = event.content;
      } else if (event.name == 'bill') {
        this.metadata.bill = event.content;
      } else if (event.name == 'suggest_replies') {
        this.metadata.replies = event.content;
      } else {
        //console.log("Event", event);
      }
    },
    save: function() {
      if (!this.entry.id) return;
      this.app.api.send('/store/update', {
        id: this.entry.id,
        name: this.entry.name,
        content: this.entry.content,
        pinned: this.entry.pinned,
        metadata: JSON.stringify(this.metadata),
      });
    },
    sendMessage: function() {
      let messages = [{role: 'user', content: this.entry.name}];
      let model = 'message';
      let req = this.app.api.completion(messages, model, {temperature: 0.2});
      let res = new StreamResponse(this.onResponseEvent.bind(this));
      this.entry.content = '';
      this.running = true;
      req.run((line) => {
        res.add(line);
      }).then((r) => {
        this.app.api.send('/store/update', {
          id: this.entry.id, name: this.entry.name, content: this.entry.content,
          metadata: JSON.stringify(this.metadata),
        });
      }).catch((err) => {
        console.log("Error!", err);
      }).finally(() => {
        this.running = false;
        this.save();
      });
    },
    onMinimize: function() {
      this.metadata.view = this.metadata.view == 'sm' ? 'reg' : 'sm';
      this.save();
    },
    onPin: function() {
      this.metadata.pinned = !this.metadata.pinned;
      this.save();
    },
    onPaste: function(evt) {
      let value = evt.clipboardData.getData('text/html');
      if (!value) value =evt.clipboardData.getData('text');
      console.log(value);
      this.app.api.send("/tools/markdown", {
        content: value,
      }).then((r) => {
        this.entry.name = r.content;
      });
      evt.preventDefault();
    },
    onShowMessage: function() {
      this.app.open_modal({
        cmp: ModalDoc,
        content: this.entry.name,
        style: {width: '95%', height: '90vh'},
        multiline: true,
      });
    },
  },
  beforeUnmount: function() {
  },
  created: function() {
    let md;
    try {
      md = JSON.parse(this.entry.metadata);
    } catch {}
    this.metadata = Settings.get_settings(md, {
      ...{category: '', replies: '', bill: ''},
      ...JSON.parse(Settings.stream_settings),
    });
  },
}
</script>

<template>
<div class="flex-x my-3">
  <div class="card flex-grow px-3"
      :class="metadata.small ? 'text-sm' : ''">
    <div class="flex-x mb-2" v-if="!is_new">
      <svg-icon name="loader" size="16" v-if="running" class="rotate mr-2"></svg-icon>
      <button @click="sendMessage" class="btn-plain muted mr-2 btn flex-x flex-ctr mr-2" v-if="!running">
        <svg-icon class="mr-2" name="play"></svg-icon>
        Replay
      </button>
      <div v-if="metadata.category"><strong>{{ metadata.category }}</strong></div>
      <div class="flex-grow"></div>
      <button @click="$emit('delete')" class="btn btn-plain flex-x flex-ctr mr-2" v-if="!running">
        <svg-icon class="" name="x-light"></svg-icon>
      </button>
      <button @click="onMinimize" class="btn btn-plain flex-x flex-ctr mr-2">
        <svg-icon class="" name="minimize-2"></svg-icon>
      </button>
      <button @click="onPin" class="btn btn-plain flex-x flex-ctr"
          :class="metadata.pinned ? 'btn-pri' : ''" v-if="false">
        <svg-icon class="" name="star" :invert="metadata.pinned"></svg-icon>
      </button>
    </div>
    <div class="mx-2 text mt-1 mb-2">
      <div style="white-space: pre-wrap">{{ entry.content }}</div>
      <div v-if="metadata.replies">
        <h4>Suggested Replies</h4>
        <div v-html="app.markdown(metadata.replies)"></div>
      </div>
      <div v-html="app.markdown(metadata.bill)"></div>
    </div>

    <div v-if="entry.content">
      <div style="max-height: 140px; overflow: hidden; border-bottom-style: dashed;"
          class="clickable border round-lg b-1 px-1 mb-2"
          @click="onShowMessage"
          v-html="app.markdown(entry.name)">
      </div>
    </div>
    <div class="flex-x flex-grow" style="position: relative; font-size: 8px;" v-else>
      <AutoTextarea classes="form-control flex-grow" class="flex-grow" xrows="3" v-model="entry.name"
          @paste="onPaste"
          styles="border-color: #0000; box-shadow: none;"
          :class="is_new ? 'text-xl' : 'text'"
          placeholder="Paste an email or other message you'd like to save here.">
      </AutoTextarea>
    </div>
    <div v-if="is_new" class="flex-x flex-grow mt-2" style="text-align: right;">
      <button @click="onInitialSave" class="btn btn-pri text-lg">Send</button>
      <button @click="$emit('delete', {skip_confirm: true})" class="btn text-lg ml-3">Cancel</button>
    </div>
  </div>
</div>
</template>
