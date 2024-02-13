<script>
import {AIChatJob, FindListItems} from '../lib/ai-job.js';
import PromptEntry from './prompt-entry.vue';
import TextInput from './modal-text-input.vue'

export default {
  props: ['app', 'item', 'level'],
  components: {PromptEntry},
  data() {
    return {
      chains: this.app.chains,
      prompt_test_sys: '',
      prompt_test: '',
      new_todo: '',
      chain_data: '',
      chain_name: '',
    } 
  },  
  methods: {
    onTestPrompt: function() {
      let prompt = this.prompt_test;
      let job = new AIChatJob(this.app, {summary: 'Running test prompt...'});
      if (this.prompt_test_sys) {
        job.add_message(this.prompt_test_sys, "system")
      }
      job.add_message(
        prompt
      );
      let full_job = this.app.ai_queue.add_job(job.run.bind(job), {priority: 5});
      this.app.ai_log.push({job: full_job, request: job});
      console.log(job);
    },
    onLoadChain: function() {
      this.app.add_chain(this.chain_name, JSON.parse(this.chain_data));
      //this.chains[this.chain_name] = this.app.chainer.import_chain(this.app, JSON.parse(this.chain_data));
    },
    onExportChain: function(chain) {
      let data = chain.export_chain();
      this.app.open_modal({
        title: 'Prompt Export',
        content: JSON.stringify(data),
        multiline: true,
        cmp: TextInput,
        hide_save: true,
        onSave: (content) => {},
      });
    },
    onCreateChain: function() {
      this.app.open_modal({
        title: 'Create Chain',
        content: 'Title',
        cmp: TextInput,
        onSave: (content) => {
          console.log(content);
          let chain = new this.app.chainer(this.app, {title: content});
          let p = chain.register({log: 'Start chain ' + content,
            inputs: ['message'], outputs: [{name: 'result', store_response: true}],
            prompt: `You are a helpful assistant.\n\nMessage:\n\`\`\`\n{{message}}\n\`\`\`\n\n(Tell it what to do)`,
          });
          chain.entrypoint(p.id, {
            map: {message: 'message'},
          });
          this.app.add_chain(content, chain.export_chain());
        },
      }); 
    },  
  },
  beforeUnmount: function() {
  },
  created: function() {
  },
}
</script>

<template>
<div class="card mx-2 mb-2 flex-x flex-grow flex-stretch bg-sec pt-2">
  <div class="flex-grow flex-y mr-2" style="overflow-y: auto;">
    <div class="flex-scroll-y pr-1">
      <div class="bg-sec p-2">
        <h4 class="my-1">Prompt Test</h4>
        <small>System</small>
        <div class="bg-sec flex-x mb-1">
          <textarea class="form-control flex-grow mb-2" rows="5" v-model="prompt_test_sys"></textarea>
        </div>
        <small>User</small>
        <div class="bg-sec flex-x mb-2">
          <textarea class="form-control flex-grow" rows="5" v-model="prompt_test"></textarea>
        </div>
        <button @click="onTestPrompt" class="btn btn-pri">Send</button>
      </div>
      <div class="bg-sec p-2">
        <h4 class="my-1">Chain Import</h4>
        <div class="bg-sec flex-x mb-2">
          <textarea class="form-control flex-grow" rows="5" v-model="chain_data"></textarea>
        </div>
        <div class="bg-sec flex-x mb-2">
          <input class="form-control flex-grow" v-model="chain_name" />
        </div>
        <button @click="onLoadChain" class="btn btn-pri">Load Chain</button>
      </div>
      <div class="flex-x">
        <div class="flex-grow"></div>
        <div>
          <button @click="onCreateChain" class="btn btn-pri">Create Chain</button>
        </div>
      </div>
      <div class="mx-2 p-3 round-sm">
        <div v-for="chain in chains">
          <div class="flex-x">
            <h3 class="mt-2 mb-1">Chain: {{chain.title}}</h3>
            <div class="flex-grow"></div>
            <div>
              <button @click="onExportChain(chain)" class="btn">Export</button>
            </div>
          </div>
          <div v-for="entry in chain.entry_points">
            <PromptEntry :app="app" :entry="entry" :level="1" :chain="chain">
            </PromptEntry>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>
