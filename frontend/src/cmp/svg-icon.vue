<script>

export default {
  props: ['app', 'name', 'size', 'invert'],
  data() {
    return {
    } 
  },  
}
</script>

<template>
<img :src="'/icons/' + name + '.svg'"
    :class="invert ? 'ico-invert' : 'ico'"
    :style="{height: (size || 14) + 'px'}" />
</template>
