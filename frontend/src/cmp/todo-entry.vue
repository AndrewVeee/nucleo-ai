<script>
import {AIChatJob, FindListItems} from '../lib/ai-job.js';

export default {
  name: 'TodoEntry',
  props: ['app', 'item', 'level'],
  components: {},
  data() {
    return {
      lvl: this.level || 0,
      children: this.item.children,
    } 
  },  
  methods: {
    onCompleteTodo: function() {
      let todo_task = '';
      let p = this.item.parent;
      while (p) {
        todo_task = '- ' + p.entry.text + ' ';
        p = p.parent;
      }
      //if (todo_task.length) todo_task += ': ';
      //todo_task += this.item.entry.text;
      let job = new AIChatJob(this.app);
      job.add_message(
          "Let's finish this to do task for the user.\n\n" +
          "Write the result of the To Do Task below so the user can mark this task as completed.",
          'system'
      )
      job.add_message(
        (todo_task.length ? 'To Do Category: ' + todo_task + "\n" : '') +
        "To Do Task:\n" + this.item.entry.text
      );
      let full_job = this.app.ai_queue.add_job(job.run.bind(job), {priority: 5});
      this.app.ai_log.push({job: full_job, request: job});
      full_job.promise.then((r) => {
        r = job.response;
        this.app.db.store.create({type: 'todo', text: r, pid: this.item.id, meta: {}}).then((r) => {
          this.item.add(r);
        });
        /*let items = FindListItems(r);
        //console.log("Finished todo", job.messages, "\n", items);
        items.forEach((c) => {
          this.app.db.store.create({type: 'todo', text: c, pid: this.item.id, meta: {}}).then((r) => {
            console.log("Created", r);
            this.item.add(r);
          });
        });
        */
      });
    },
    onFillTodo: function() {
      let todo_task = '';
      let p = this.item.parent;
      while (p) {
        todo_task = '- ' + p.entry.text + ' ';
        p = p.parent;
      }
      //if (todo_task.length) todo_task += ': ';
      //todo_task += this.item.entry.text;
      let job = new AIChatJob(this.app);
      job.add_message(
          "Let's help the user break down this to do task." +
          "Make a bullet list of up to 5 tasks to complete the item below.\n\n" +
          "Keep each entry short. One sentence at most, and short, like: 'Go to grocery store.' or 'Write a short document.'",
          'system'
      )
      job.add_message(
        (todo_task.length ? 'To Do Category: ' + todo_task + "\n" : '') +
        "To Do Task:\n" + this.item.entry.text
      );
      let full_job = this.app.ai_queue.add_job(job.run.bind(job), {priority: 5});
      this.app.ai_log.push({job: full_job, request: job});
      full_job.promise.then((r) => {
        r = job.response;
        let items = FindListItems(r);
        //console.log("Finished todo", job.messages, "\n", items);
        items.forEach((c) => {
          this.app.db.store.create({type: 'todo', text: c, pid: this.item.id, meta: {}}).then((r) => {
            console.log("Created", r);
            this.item.add(r);
          });
        });
      });
    },
    delete_entries: function(entries) {
      for (let ent of entries) {
        console.log("Delete", ent.entry.text);
        this.delete_entries(ent.children);
        ent.entry.destroy();
      }
    },
    onDelete: function(child,idx) {
      this.children.splice(idx, 1);
      this.delete_entries(child.children);
      child.entry.destroy();
    },
  },
  beforeUnmount: function() {
  },
  created: function() {
  },
}
</script>

<template>
<div class="mb-0"
    :style="{paddingLeft: (lvl * 10) + 'px'}">
  <div class="flex-x mt-1 mb-2 pl-1">
    <div style="white-space: pre-wrap">
      {{item.entry.text}}
    </div>
    <div class="flex-grow"></div>
    <button @click="onFillTodo(todo)" class="btn btn-sm ml-2">Break it Down</button>
    <button @click="onCompleteTodo(todo)" class="btn btn-sm ml-2">Complete</button>
    <button @click="$emit('delete')" class="btn btn-sm ml-2">Delete</button>
  </div>
  <todo-entry :key="child.id" v-for="child,idx in children"
      @delete="onDelete(child,idx)"
      :app="app" :item="child" :level="(level || 0) + 1">
  </todo-entry>
</div>
</template>
