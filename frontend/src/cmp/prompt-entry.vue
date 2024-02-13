<script>
import TextInput from './modal-text-input.vue'

export default {
  name: 'PromptEntry',
  props: ['app', 'entry', 'level', 'chain'],
  components: {},
  data() {
    return {
      lvl: this.level || 0,
      //children: this.item.children,
    } 
  },  
  methods: {
    onEditLog: function() {
      this.app.open_modal({
        title: 'Edit Title',
        content: this.entry.prompt.log,
        cmp: TextInput,
        onSave: (content) => {
          this.entry.prompt.log = content;
        },
      });
    },
    onEditPrompt: function() {
      this.app.open_modal({
        title: 'Edit Prompt',
        content: this.entry.prompt.prompt_entry.prompt,
        cmp: TextInput,
        multiline: true,
        onSave: (content) => {
          this.entry.prompt.prompt_entry.prompt = content;
        },
      });
    },
    onAddChild: function() {
      this.app.open_modal({
        title: 'Add Child',
        content: 'Title',
        cmp: TextInput,
        onSave: (content) => {
          console.log(content);
          let p = this.chain.register({log: content,
            inputs: ['message'], outputs: [{name: 'result', store_response: true}],
            prompt: `You are a helpful assistant.\n\nMessage:\n\`\`\`\n{{message}}\n\`\`\`\n\n(Tell it what to do)`,
          });
          this.entry.entrypoint(p.id, {
            map: {message: 'message'},
          });
        },
      });
    },
    onAddCond: function() {
      this.entry.conditions.push({op: '==', name: 'msg_category', value: 'personal'});
    },
  },
  beforeUnmount: function() {
  },
  created: function() {
  },
}
</script>

<template>
<div class="mb-3"
    :style="{paddingLeft: (lvl * 20) + 'px'}">
  <div class="flex-x mt-1 pl-1">
    <div class="flex-grow">
      <div class="clickable text-lg mb-1"
          @click="onEditLog"
      >
        <strong>&bull; Prompt: {{entry.prompt.log}}</strong>
      </div>
      <div>
        <div><span>Conditions:</span></div>
        <div v-for="cond in entry.conditions" class="ml-2 my-1">
          <span v-if="false">If: {{cond.name}} {{cond.op}} {{cond.value}}</span>
          If
          <input class="form-control" type="text" v-model="cond.name" />
          <select class="form-control mx-2" v-model="cond.op">
            <option value="==">Is Equal To</option>
            <option value="!=">Is Not Equal To</option>
            <option value="include">Includes</option>
            <option value="exclude">Does Not Include</option>
          </select>
          <input class="form-control" type="text" v-model="cond.value" />
        </div>
        <button @click="onAddCond" class="ml-2 btn btn-sm">Add Condition</button>
      </div>
      <div class="mt-1">
        <span>Inputs:</span>
        <div class="ml-2">{{entry.fields}}</div>
      </div>
      <div class="mt-1">
        <div><span>Outputs:</span></div>
        <div v-for="out in entry.prompt.prompt_entry.outputs" class="ml-2">
          <span v-if="app.debug">{{out}}</span>
          <div>
          Name: <input v-model="out.name" class="form-control" />
          Parser:
          <select class="form-control" v-model="out.parser">
            <option value="full_response">Full Response</option>
            <option value="from_line">Match Line Start</option>
          </select>
          <span v-if="out.parser == 'from_line'">
            Line Match (all lowercase): <input v-model="out.parser_ex" class="form-control" />
          </span>
          Event: <input v-model="out.event" class="form-control" />
          </div>
        </div>
      </div>
      <div class="mt-1">Prompt</div>
      <div class="my-1 clickable bg-sec round-lg xborder p-1 text-sm" style="xwhite-space: pre-wrap; max-height: 6.5em; overflow: hidden;"
          @click="onEditPrompt"
        >{{entry.prompt.prompt_entry.prompt}}</div>
    </div>
  </div>
  <prompt-entry :key="child.id" v-for="child,idx in entry.entry_points"
      :chain="chain"
      :app="app" :entry="child" :level="lvl + 1">
  </prompt-entry>
  <button @click="onAddChild" class="btn">Add Child to: {{entry.prompt.log}}</button>
</div>
</template>
