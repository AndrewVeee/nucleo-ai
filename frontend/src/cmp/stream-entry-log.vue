<script>

export default {
  props: ['app', 'entry'],
  data() {
    return {
      metadata: {},
      is_new: this.entry.content ? false : true,
    } 
  },  
  methods: {
    onOpen: function() {
      // TODO: App needs to cache or look up the meta entry id
      console.log("Open", this.metadata);
      this.app.open_entry_id(this.metadata.id);
    },
  },
  beforeUnmount: function() {
  },
  created: function() {
    try {
      this.metadata = JSON.parse(this.entry.metadata);
    } catch {}
  },
}
</script>

<template>
<div class="flex-x mt-1">
  <div class="flex-x flex-grow text-center text-sm">
    <div class="flex-grow text-center text-sm" style="line-height: 1;">
      <span class="mr-2" style="font-weight:300;">Your assistant created a new {{ metadata.type }}:</span>
      <span @click="onOpen" class="clickable p-1 xpx-2">{{ entry.name }}</span>
      
      <button class="btn btn-plain btn-sm ml-2"
          @click="$emit('delete', {skip_confirm: true})">
        <svg-icon name="x-light" :size="14"></svg-icon>
      </button>
    </div>
    <div>
    </div>
  </div>
</div>
</template>
