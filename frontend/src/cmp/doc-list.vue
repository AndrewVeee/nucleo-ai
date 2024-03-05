<script>
import ModalTextInput from './modal-text-input.vue';
import ModalConfirm from './modal-confirm.vue';

export default {
  props: ['app', 'item', 'level'],
  components: {ModalConfirm},
  data() {
    return {
      new_doc: '',
      processing: false,
      uploads: [],
    } 
  },  
  methods: {
    create_doc: function(title, content, opts) {
      if (!opts) opts = {};
      //this.processing = "Saving doc: " + title;
      let p = this.app.api.send('/store/create', {
        data_type: 'doc',
        name: title,
        content: content,
        source: opts.source,
      }).then((r) => {
        this.app.doc_list.unshift(r);
        this.new_doc = '';
        if (!content) this.onEdit(r);
      }).finally(() => { this.processing = false;});

      this.uploads.unshift({p: p, status: 'Creating doc: ' + title});
      p.finally((r) => { this.removeUploadPromise(p)});
      return p;
    },
    addDoc: function() {
      let title = this.new_doc, content = '';
      if (/^https?:\/\//.exec(this.new_doc)) {
        let p = new Promise((res, rej) => {
          this.app.api.send('/tools/url_to_md', {
            url: this.new_doc,
          }).then((r) => {
            if (!r.title) {
              r.title = r.content.split("\n")[0].slice(0, 45);
            }
            this.create_doc(r.title, r.content, {source: this.new_doc}).finally(() => {
              this.removeUploadPromise(p);
              res();
            });
          }).catch((err) => { rej(); });
        });
        this.uploads.unshift({p: p, file: this.new_doc, status: ''});
        p.finally((r) => { this.removeUploadPromise(p)});
        return;
      }
      this.create_doc(this.new_doc, '');
    },
    performDelete: function(entry, idx) {
      this.app.api.send('/store/delete', {id: entry.id}).then((r) => {
        this.app.doc_list.splice(idx, 1);
      });
    },
    onDelete: function(entry,idx) {
      this.app.open_modal({
        title: 'Delete Doc?',
        cmp: ModalConfirm,
        message: "Are you sure you want to delete the document " + entry.name + "?",
        onConfirm: () => { this.performDelete(entry, idx) },
      });
    },
    onEdit: function(entry) {
      this.app.api.send('/store/list', {id: entry.id}).then((r) => {
        r = r[0];
        if (!r) return;
        this.app.open_modal({
          title: entry.name,
          cmp: ModalTextInput,
          content: r.content,
          multiline: true,
          style: {width: '85%', height: '85vh'},
          onSave: (content) => {
            this.app.api.send('/store/update', {
              id: entry.id,
              content: content,
            }).then((r) => { entry.content = content; });
          },
        });
      });
    },
    onShowDoc: function(doc) {
      this.app.open_entry_id(doc.id);
    },
    removeUploadPromise: function(p) {
      for (let idx in this.uploads) {
        if (this.uploads[idx].p == p)
          this.uploads.splice(idx, 1);
      }
    },
    uploadFile: function(file) {
      let p = this.app.api.upload('/store/upload', {file: file}, {
        no_ct: true,
      }).then((r) => {
        this.app.doc_list.unshift(r);
      });

      this.uploads.unshift({p: p, file: file.name});
      p.finally((r) => { this.removeUploadPromise(p)});
      return p;
    },
    onDropFile: function(evt) {
      evt.preventDefault();
      let p = [];
      for (let item of evt.dataTransfer.items) {
        let file = item.getAsFile();
        console.log("File", file);
        p.push(this.uploadFile(file));
      }
    },
    onSelectFile: function(evt) {
      let p = [];
      for (let item of this.$refs.files.files) {
        p.push(this.uploadFile(item));
      }
      this.$refs.files.multiline = '';
    },
  },
  beforeUnmount: function() {
  },
  created: function() {
  },
}
</script>

<template>
<div class="mb-2 flex-x flex-grow flex-stretch pt-2">
  <div class="flex-grow flex-y" style="overflow-y: auto;">
    <div class="flex-x px-3 mx-2">
      <div class="flex-grow p-rel flex-x">
        <input class="form-control flex-grow" v-model="new_doc"
            placeholder="Enter a title to create a new doc, or a URL to convert a web page."
            @keypress.enter="addDoc()"/>
      </div>
      <div class="ml-1">
        <button @click="addDoc()" class="btn">Add</button>
      </div>
    </div>
    <div v-if="processing !== false" class="mx-3">
      <svg-icon name="loader" size="16" class="rotate mr-3"></svg-icon>
      <span>{{ processing }}</span>
    </div>
    <div style="border: 2px dashed var(--accent-color)" class="muted clickable p-2 text-center mx-3 my-2 text-sm"
        @drop="onDropFile"
        @dragover="$event.preventDefault()"
        @click="$refs.files.click()">
      <input @input="onSelectFile" multiple="true" type="file" ref="files" style="display: none;" />
      Drag files or click to upload.
    </div>
    <div v-for="up in uploads" class="mx-3">
      <svg-icon name="loader" size="16" class="rotate mr-1"></svg-icon>
      {{ up.status || up.file }}
    </div>
    <div class="flex-scroll-y" v-if="app.doc_list">
      <div class="mx-2 p-2">
        <div :key="entry.id" class="card round-lg mx-2 mb-3" v-for="entry,idx in app.doc_list"
            style="display: inline-block; vertical-align: top;">
          <div @click="onShowDoc(entry)" class="clickable text-sm"
              style=" width: 125px; height: 75px; overflow: hidden; word-break: break-word">
            {{ entry.name }}
          </div>
          <div class="mt-2 flex-x">
            <svg-icon title="Created by your assistant." name="assistant" class="muted" size="12" v-if="entry.ai_created"></svg-icon>
            <div class="flex-grow"></div>
            <button @click="onEdit(entry)" class="btn btn-sm btn-plain">
              <svg-icon name="edit" size="12"></svg-icon>
            </button>
            <button class="btn btn-sm btn-plain"
                @click="onDelete(entry,idx)">
              <svg-icon name="trash" size="12"></svg-icon>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>
