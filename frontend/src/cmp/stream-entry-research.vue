<script>
import {StreamResponse} from '../lib/api.js';
import * as Settings from '../lib/meta-settings.js';
import ModalDoc from './modal-doc.vue';

export default {
  props: ['app', 'entry'],
  data() {
    return {
      metadata: {},
      is_new: this.entry.name ? false : true,
      new_step: 1,
      gen_topics: false,
      running: false,
      live_response: null,
      live_content_id: null,
      live_content: '',
      full_content: null,
      max_time: 0,
      time_left: 0,
    } 
  },  
  methods: {
    onInitialSave: function() {
      this.app.api.send('/store/update', {
        id: this.entry.id,
        name: this.entry.name,
        metadata: JSON.stringify(this.metadata),
      }).then((r) => {
        this.is_new = false;
      });
      this.sendMessage();
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
      let model = "assistant";
      let req = this.app.api.completion(messages, model, {temperature: 0.2});
      let res = new StreamResponse(this.onResponseEvent.bind(this));
      this.entry.content = '';
      //this.$set(response, 'info', res);
      this.running = true;
      req.run((line) => {
        res.add(line);
      }).then((r) => {
        this.save();
      }).catch((err) => {
        console.log("Error!", err);
      }).finally(() => {
        console.log("Finished");
        this.running = false;
      });
    },
    onResponseEvent: function(event) {
      if (event.name != 'live_content') {
        console.log("Event", event);
      }
      if (event.name == 'content') {
        this.entry.content += event.content;
      } else if (event.name == 'new_entry') {
        console.log(event);
        //this.app.add_entry(event.content);
      } else if (event.name == 'live_content') {
        //console.log(event);
        if (this.live_content_id != event.content.id) this.live_content = '';
        this.live_content_id = event.content.id;
        this.live_content += event.content.text;
      } else if (event.name == 'document') {
        this.full_content = event.content.content;
      } else if (event.name == 'time') {
        this.time_left = event.content.left;
        this.max_time = event.content.total;
      }
    },
    startResearch: function() {
      let topic_list = this.metadata.topics.filter((ent) => { return ent != ''});
      let messages = [
        {role: 'config', content: JSON.stringify({
          topic: this.entry.name,
          topics: topic_list,
          priority: 5,
          ...this.metadata.config,
        })},
      ];
      let req = this.app.api.completion(messages, 'researcher');
      let res = this.live_response = new StreamResponse(this.onResponseEvent.bind(this));
      this.running = true;
      this.save();
      req.run((line) => {
        res.add(line);
      }).then((r) => {
        console.log("Research finished!");
        let name = this.entry.name;
        if (this.metadata.entries.length > 1) name += ' ' + (this.metadata.entries.length + 1);
        this.app.api.send('/store/create', {
          data_type: 'doc',
          name: name,
          content: this.full_content,
          ai_created: true,
          metadata: '{}',
        }).then((r) => {
          this.metadata.entries.unshift({id: r.id, name: r.name});
          this.app.doc_list.unshift({id: r.id, data_type: 'doc', name: r.name});
          this.save();
          this.is_new = false;
          this.app.open_entry_id(r.id);
        }).catch((err) => {
          console.log("Save error", err);
        });
      }).catch((err) => {
        console.log("Research error:", err);
      }).finally(() => {
        this.running = false;
        this.live_response = null;
      });
    },
    onInitialSearch: function() {
      let messages = [
        {role: 'config', content: JSON.stringify({
          topic: this.entry.name,
        })},
      ];
      let req = this.app.api.completion(messages, 'researcher');
      let res = new StreamResponse();
      this.gen_topics = true;
      req.run((line) => {
        res.add(line);
      }).then((r) => {
        this.metadata.topics = res.response.split("\n");
        this.new_step = 2;
        this.save();
      }).catch((err) => {
        console.log("Error!", err);
      }).finally(() => { this.gen_topics = false; });
    },
    onMinimize: function() {
      this.metadata.view = this.metadata.view == 'sm' ? 'reg' : 'sm';
      this.save();
    },
    onPin: function() {
      this.entry.pinned = !this.entry.pinned;
      this.save();
    },
    onCancel: function() {
      if (this.metadata.entries.length > 0) {
        this.is_new = false;
      } else {
        this.$emit('delete', {skip_confirm: true})
      }
    }
  },
  beforeUnmount: function() {
  },
  created: function() {
    if (!this.entry.name) this.entry.name = '';
    if (!this.entry.content) this.entry.content = '';
    let md;
    try {
      md = JSON.parse(this.entry.metadata);
    } catch {}
    this.metadata = Settings.get_settings(md, {
      ...JSON.parse(Settings.stream_settings),
      ...{
        topics: [],
        entries: [],
        config: {
          websearch: true,
          subtopic_count: 3,
          max_depth: 2,
          max_time: 3,
          temperature: 0,
          paragraphs: 2,
          writing_style: '',
        },
      }
    });
  },
}
</script>

<template>
<div class="flex-x my-3">
  <div class="card flex-grow"
      :class="metadata.view == 'sm' ? 'text-xs' : ''">
    <div class="flex-x mb-2" v-if="metadata.entries.length > 0">
      <svg-icon name="loader" size="16" v-if="running" class="rotate"></svg-icon>
      <button @click="is_new=true; new_step=2" class="btn-plain muted mr-2 btn flex-x flex-ctr" v-if="!running">
        <svg-icon class="mr-2" name="play"></svg-icon>
        Replay
      </button>
      <div class="flex-grow"></div>
      <button @click="$emit('delete')" class="btn btn-plain flex-x flex-ctr mr-2" v-if="!running">
        <svg-icon class="" name="x"></svg-icon>
      </button>
      <button @click="onMinimize" class="btn btn-plain flex-x flex-ctr mr-2"
          :class="metadata.view == 'sm' ? 'btn-pri' : ''">
        <svg-icon class="" :invert="metadata.view == 'sm'" name="minimize-2"></svg-icon>
      </button>
      <button @click="onPin" class="btn btn-plain flex-x flex-ctr"
          :class="entry.pinned ? 'btn-pri' : ''" v-if="false">
        <svg-icon class="" name="star" :invert="entry.pinned"></svg-icon>
      </button>
    </div>
    
    <h4 v-if="entry.name">{{ entry.name }}</h4>
    
    <div v-if="is_new && !live_response">
      <div v-if="new_step == 1">
        <p>
          In-depth web researcher for any topic.
        </p>
        <AutoTextarea classes="form-control flex-grow" class="flex-grow" xrows="3"
            v-model="entry.name"
            :class="is_new ? 'text-xl' : (metadata.view == 'sm' ? 'text-xs' : '')"
            placeholder="What topic do you want to research?">
        </AutoTextarea>
        <div v-if="gen_topics" class="my-2">
          <svg-icon name="loader" size="16" class="rotate"></svg-icon>
          Generating initial topics.
        </div>
        <div class="flex-x flex-grow mt-2" style="text-align: right;" v-else>
          <button @click="onInitialSearch" class="btn btn-pri text-lg">Next</button>
          <button @click="onCancel" class="btn text-lg ml-3">Cancel</button>
        </div>
      </div>
      <div v-if="new_step == 2">
        <p>How does this research list look? Edit, remove, or add topics below.</p>
        <div v-for="topic,idx in metadata.topics" class="flex-x px-2 mb-2">
          <input class="form-control flex-grow" v-model="metadata.topics[idx]" />
        </div>
        <div class="mt-3">
          <button @click="startResearch" class="btn btn-pri mr-2">Start Research!</button>
          <button @click="new_step = 1" class="btn mr-2">Back - Edit Topic</button>
          <button @click="onCancel" class="btn">Cancel</button>
        </div>

        <h5>Settings</h5>

        <div class="mt-2">Max Section Depth: {{ metadata.config.max_depth }}</div>
        <div class="flex-x">
          <input type="range" class="flex-grow" min="1" max="5" v-model="metadata.config.max_depth" />
        </div>
        <div class="mt-2">Max Research Time (Minutes): {{ metadata.config.max_time}}</div>
        <div class="flex-x">
          <input type="range" class="flex-grow" min="0.5" max="10" step="0.25" v-model="metadata.config.max_time" />
        </div>
        <div class="mt-2">Subtopic Count: {{ metadata.config.subtopic_count}}</div>
        <div class="flex-x">
          <input type="range" class="flex-grow" min="1" max="10" step="1" v-model="metadata.config.subtopic_count" />
        </div>
        <div class="mt-2">Paragraphs per Section: {{ metadata.config.paragraphs}}</div>
        <div class="flex-x">
          <input type="range" class="flex-grow" min="1" max="10" step="1" v-model="metadata.config.paragraphs" />
        </div>
        <div class="mt-2">Temperature: {{ metadata.config.temperature}}</div>
        <div class="flex-x">
          <input type="range" class="flex-grow" min="0.0" max="2" step="0.01" v-model="metadata.config.temperature" />
        </div>
        <label class="flex-x mt-2">
          <input type="checkbox" v-model="metadata.config.websearch" /> Search the web for each section.
        </label>
      </div>
    </div>
    <div v-else>
      <div v-if="metadata.entries">
        <button class="btn btn-plai mr-2"
            @click="app.open_entry_id(entry.id)"
            v-for="entry in metadata.entries">
          {{ entry.name }}
        </button>
      </div>
      <div v-if="false && live_response">
        <div>
          <div>State: {{ live_response.state  }}</div>
          <div>Status: {{ live_response.status  }}</div>
        </div>
        <div v-for="entry in live_response.entries" style="display: inline-block;"
            v-if="entry.data_type != 'stream'"
            @click="app.open_entry(entry)"
            class="clickable text-sm bg-sec mr-2">
          New {{ entry.data_type }}
        </div>
        <button @click="onShowLog(log)" class="btn btn-sm ml-2">⛶</button>
      </div>
    </div>
    <div v-if="live_response">
      <div class="my-2">
        Research Time Remaining: {{parseInt(time_left)}} / {{parseInt(max_time)}}
      </div>
      <div v-if="false" class="my-2">State: {{ live_response.state  }}</div>
      <div class="my-2">Status: {{ live_response.status  }}</div>

      Live Preview:
      <div class="flex-x text-muted my-2 p-2" style="height: 5rem; border: 1px solid #ccc; overflow: hidden">
        <div style="align-self: end;  white-space: pre-wrap">{{ live_content }}</div>
      </div>

    </div>
  </div>
</div>
</template>
