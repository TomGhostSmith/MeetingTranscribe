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
                      @timeupdate="onTimeUpdate"
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
        <div style="text-align: left; padding: 20px">
          <div v-for="(seg, t) in scripts" :key="t" >
            <p class="speaker">{{ seg[0] }}: </p>
            <p>
              <span class="script" v-for="(s, t) in seg[1]" :key="t" :style="getColor(s[1], s[2])" @click="jumpTo(s[1])">{{ s[0] + ' ' }}</span>
            </p>
          </div>
        </div>
        
      </el-aside>
    </pane>
    
  </splitpanes>
</template>

<!-- <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script> -->
<script>
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'
import Hls from 'hls.js';
export default {
  components: { Splitpanes, Pane },
  name: 'HelloWorld',
  data() {
      return {
          fileName: "1",
          scripts: [],
          hls: null,
          currentTime: 0
      }
  },
  methods: {
      getColor(t1, t2)
      {
        
        let _this = this        
        if ((t1 <= _this.currentTime) && (t2 > _this.currentTime))
        {
          return {background: "#fbbf69"}
        }
        else
        {
          return {}
        }
      },
      onTimeUpdate() {
        
        this.currentTime = this.$refs.videoRef.currentTime;
        // console.log(this.currentTime);
      },
      jumpTo(t){
        this.$refs.videoRef.currentTime = t
      }
  },
  mounted(){
    let _this = this
    console.log(this);
    console.log(_this.$backend);
    
    
    console.log("Hi");
    const video = _this.$refs.videoRef
    let videoSrc = _this.$backend.value + '/file/' + _this.fileName + '.m3u8'

    console.log(videoSrc);
    

    if (Hls.isSupported()) {
      console.log("Hello");
      this.hls = new Hls()
      this.hls.loadSource(videoSrc)
      this.hls.attachMedia(video)
      this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
        this.hls.subtitleTrack = 0;
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

    this.$axios.get(_this.$backend.value + "/api/getScript/" + _this.fileName).then(resp => {
      if (resp.status === 200){
        _this.scripts = resp.data
        
        
      }
      else
      {
        console.log(resp);
        
      }
    })
  },
  beforeUnmount(){
    if (this.hls) {
      this.hls.destroy();
    }
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

.speaker{
  font-size: 20px
}
.script{
  cursor: pointer;
  font-size: 18px
}

.script:hover
{
  background-color: #97c7f7;
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