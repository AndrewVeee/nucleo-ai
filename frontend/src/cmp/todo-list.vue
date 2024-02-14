<script>
import InlineEditor from './inline-editor.vue';

export default {
  props: ['app', 'item', 'level'],
  components: {InlineEditor},
  data() {
    return {
      todo_list: this.app.todo_list,
      new_todo: '',
      edit_id: null,
    } 
  },  
  methods: {
    addToDo: function() {
      this.app.api.send('/store/create', {
        data_type: 'todo',
        name: this.new_todo,
      }).then((r) => {
        this.app.todo_list.unshift(r);
        this.new_todo = '';
      });
    },
    onUpdateEntry: function(entry, evt) {
      this.app.api.send('/store/update', {
        id: entry.id,
        name: evt,
      }).then((r) => {
        entry.name = r.name;
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
      this.todo_list.roots.splice(idx, 1);
      this.delete_entries(child.children);
      child.entry.destroy();
    },
    onDelete: function(entry, idx) {
      this.app.api.send('/store/delete', {id: entry.id}).then((r) => {
        this.app.todo_list.splice(idx, 1);
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
<div class="mx-0 mb-2 flex-x flex-grow flex-stretch pt-2">
  <div class="flex-grow flex-y xmr-2" style="overflow-y: auto;">
    <div class="flex-x px-3 mx-2">
      <div class="flex-grow p-rel flex-x">
        <input type="text" name="todo" class="form-control flex-grow" v-model="new_todo"
            placeholder="New to do entry"
            @keypress.enter="addToDo()"/>
      </div>
      <div class="ml-1">
        <button @click="addToDo()" class="btn">Add</button>
      </div>
    </div>
    <div class="flex-scroll-y" v-if="todo_list">
      <div class="mx-2 p-3">
        <div :key="entry.id" class="card flex-x mb-2" v-for="entry,idx in app.todo_list">
          <span v-if="false">{{ entry.name }}</span>
          <InlineEditor :value="entry.name" :editing="edit_id == entry.id"
              class="flex-grow flex-x"
              ctl_class="form-control flex-grow"
              @cancel="edit_id = null"
              @edit="edit_id = entry.id"
              @save="onUpdateEntry(entry, $event)">
          </InlineEditor>
          <div class="flex-grow" v-if="false"></div>
          <svg-icon name="assistant" class="mr-2 muted" size="12" v-if="entry.ai_created"></svg-icon>
          <button class="btn btn-sm" v-if="false">Done</button>
          <button @click="onDelete(entry, idx)" class="btn btn-sm btn-plain">
            <svg-icon name="trash"></svg-icon>
          </button>
        </div>
      </div>
    </div>
  </div>
</div>
</template>
