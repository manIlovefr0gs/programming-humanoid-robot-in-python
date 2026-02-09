from naoqi import ALProxy


class VisionModule:
    
    def __init__(self, nao_config, color_name, threshold):
        self.nao = nao_config
        self.color_name = color_name
        self.threshold = threshold
        
        self.blob_proxy = None
        self.memory_proxy = None
        self._initialized = False
    
    
    def initialize(self):
        """Initialize ALColorBlobDetection with target color"""
        if self._initialized:
            return
        
        self.blob_proxy = self.nao.get_proxy("ALColorBlobDetection")
        self.memory_proxy = self.nao.get_proxy("ALMemory")
        
        # Get color from config
        if self.color_name not in self.nao.COLORS:
            raise ValueError("Color " + self.color_name + " not found in nao_config.COLORS")
        
        color_rgb_threshold = self.nao.COLORS[self.color_name]
        
        # Set color and threshold
        self.blob_proxy.setColor(color_rgb_threshold)
        self.blob_proxy.setThreshold(self.threshold)
        
        self._initialized = True
        print("[Vision] Initialized with color: " + self.color_name + ", threshold: " + str(self.threshold))
    
    
    def start(self):
        """Start blob detection"""
        if not self._initialized:
            self.initialize()
        
        self.blob_proxy.subscribe("ColorBlobTracker")
        print("[Vision] Started blob detection")
    
    
    def stop(self):
        """Stop blob detection"""
        if self.blob_proxy:
            self.blob_proxy.unsubscribe("ColorBlobTracker")
            print("[Vision] Stopped blob detection")
    
    
    def get_blob_position(self):
        """Get current blob position from memory"""
        try:
            blob_info = self.memory_proxy.getData("ColorBlobDetection/BlobInfo")
            
            if blob_info and len(blob_info) > 0:
                # blob_info structure: [x, y, width, height]
                return {
                    'detected': True,
                    'x': blob_info[0],
                    'y': blob_info[1],
                    'width': blob_info[2],
                    'height': blob_info[3]
                }
            else:
                return {'detected': False}
                
        except Exception as e:
            print("[Vision] Error getting blob position: " + str(e))
            return {'detected': False}
