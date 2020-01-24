from mojo.events import EditingTool, installTool
from AppKit import NSImage
from os import path

dirname = path.dirname(__file__)
toolbarIcon = NSImage.alloc().initByReferencingFile_(path.join(dirname, "../resources/EditVerticalMetricsTool_Icon.pdf"))

class EditVertMetrics(EditingTool):
    
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

    def becomeInactive(self):
        self.f = CurrentFont()
        
        for guideline in self.f.guidelines:
            if guideline.name in self.verts.keys():
                self.f.removeGuideline(guideline)
        
    def mouseUp(self, notification):
        self.f = CurrentFont()
        
        vert_settings = {}
        for guideline in self.f.guidelines:
            if guideline.name in self.verts.keys():
                setattr(self.f.info, self.verts[guideline.name][1], guideline.y) 
            
    def getToolbarTip(self):
        return "Edit Vertical Metrics"
        
    def getToolbarIcon(self):
        return(toolbarIcon)
        
        
installTool(EditVertMetrics())