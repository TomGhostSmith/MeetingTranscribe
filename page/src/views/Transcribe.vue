<template>
  <splitpanes style="height: 100%;">
    <pane min-size="20">
      <el-main style="height: 100%;padding:0">
          <splitpanes horizontal>
            <pane min-size="20">
                <h2>Video Title</h2>
                    <video
                    ref="videoRef"
                      controls
                      style="width: 100%; max-height: 80%;"
                    ></video>
            </pane>
            <pane min-size="20">
              <h2>Meeting info</h2>
            </pane>
          </splitpanes>
        </el-main>
      </pane>
      <pane min-size="20" max-size="60" size="20">
        <el-aside style="height: 100%; width: 100%">
        <h2>Transcript</h2>
        <p style="text-align: left; padding: 20px">Let's start the meeting</p>
        
      </el-aside>
    </pane>
    
  </splitpanes>
</template>

<!-- <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script> -->
<script>
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'
import { onMounted, ref, onBeforeUnmount } from 'vue';
import Hls from 'hls.js';
export default {
  components: { Splitpanes, Pane },
  name: 'HelloWorld',
  data() {
      return {
          machine: "Sland"
      }
  },
  methods: {
      getNetThresh(unit)
      {
          console.log();
          
          if (unit === 'KB/s') return this.NetKBThresh
          else return this.NetMBThresh
      }
  },
  setup() {
    
    const videoRef = ref(null)
    let hls = null
    
    onMounted(() => {
      console.log("Hi");
      const video = videoRef.value
      const videoSrc = 'http://10.138.42.155:8088/sample.m3u8'

      if (Hls.isSupported()) {
        console.log("Hello");
        hls = new Hls()
        hls.loadSource(videoSrc)
        hls.attachMedia(video)
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          console.log(hls.subtitleTracks);
          hls.subtitleTrack = 0;
        //   console.log("Hi!!!");
        //   video.play()
        })
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        console.log("Hello!!!");
        video.src = videoSrc
        // video.addEventListener('loadedmetadata', () => {
        //   video.play()
        // })
      }
    })
    onBeforeUnmount(() => {
      if (hls) {
        hls.destroy();
      }
    });
    return { videoRef }
  }
}

</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>

.splitpanes--vertical > .splitpanes__splitter {
  background-color: #dcdfe6; /* show a visible divider */
  width: 4px;                /* thickness of the bar */
  cursor: col-resize;        /* cursor for resizing */
  transition: background-color 0.2s;
}

.splitpanes--horizontal > .splitpanes__splitter {
  background-color: #dcdfe6; /* show a visible divider */
  height: 4px;                /* thickness of the bar */
  cursor: row-resize;        /* cursor for resizing */
  transition: background-color 0.2s;
}

.splitpanes__splitter:hover {
  background-color: #409EFF; /* highlight when hovered */
}

.fileItem{
  font-size: 20px!important;
}


#app {
    font-family: Avenir, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-align: center;
    margin: 0!important;
    height: 100%;
    /* margin-top: 100px; */
}
html, body{
  height: 100%!important;
  width: 100%!important;
  margin: 0!important;
    /* background: #42416b; */
    /* background: #8d7fa2; */
}
</style>