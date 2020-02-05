from mojo.events import EditingTool, installTool
from mojo.UI import getDefault, setDefault
from AppKit import NSImage
from os import path

dirname = path.dirname(__file__)
toolbarIcon = NSImage.alloc().initByReferencingFile_(path.join(dirname, "../resources/EditFontDimensionsTool_Icon.pdf"))

class EditFontDimensions(EditingTool):
    
    '''
    Robofont extension for visually manipulating 
    your font info’s Dimensions values.
    
    Ryan Bugden
    2020.01.24
    '''
    
    def setup(self):
        self.f = CurrentFont()
        
    def becomeActive(self):
        self.f = CurrentFont()
        
        self.verts = {
            "             "  : [self.f.info.descender, "descender"],
            "            "   : [self.f.info.xHeight,   "xHeight"],
            "           "    : [self.f.info.capHeight, "capHeight"],
            "          "     : [self.f.info.ascender,  "ascender"]
            } 
        
        for vert in self.verts.keys():
            self.f.appendGuideline(position=(0, self.verts[vert][0]), angle=0, name=vert, color=(0,0,0,1))
            
        self.user_lock = getDefault("glyphViewLockGuides")
        setDefault("glyphViewLockGuides", False)

    def becomeInactive(self):
        self.f = CurrentFont()
        
        for guideline in self.f.guidelines:
            if guideline.name in self.verts.keys():
                self.f.removeGuideline(guideline)
                
        setDefault("glyphViewLockGuides", self.user_lock)
        
    def mouseDragged(self, point, delta):
        self.setMetrics()
                
    def mouseUp(self, point):
        self.setMetrics()
                
    def setMetrics(self):
        self.f = CurrentFont()
        
        vert_settings = {}
        for guideline in self.f.guidelines:
            if guideline.name in self.verts.keys():
                setattr(self.f.info, self.verts[guideline.name][1], guideline.y) 
            
    def getToolbarTip(self):
        return "Edit Font Dimensions"
        
    def getToolbarIcon(self):
        return(toolbarIcon)
        
installTool(EditFontDimensions())