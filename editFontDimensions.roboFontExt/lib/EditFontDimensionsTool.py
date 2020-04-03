from mojo.events import EditingTool, installTool
from mojo.UI import getDefault, setDefault, CurrentGlyphWindow
from mojo.extensions import setExtensionDefault, getExtensionDefault
from AppKit import NSImage
from vanilla import CheckBox
from os import path

dirname = path.dirname(__file__)
toolbarIcon = NSImage.alloc().initByReferencingFile_(path.join(dirname, "../resources/EditFontDimensionsTool_Icon.pdf"))

class EditFontDimensions(EditingTool):
    '''
    Robofont extension for visually manipulating 
    your font info’s Dimensions values.
    
    Ryan Bugden
    1.2.1 2020.04.03
    1.2.0 2020.04.03
    1.1.1 2020.02.05
    1.0.0 2020.01.24 
    '''
    
    def setup(self):
        self.f = CurrentFont()
        
    def becomeActive(self):
        self.f = CurrentFont()
        self.w = CurrentGlyphWindow()
        self.desc_driving = False
        
        # setting up user preferences
        self.pref_key = 'com.ryanbugden.EditFontDimensions'
        
        # adding the UPM lock checkbox
        self.lock2upm = getExtensionDefault(self.pref_key, False)
        self.checkbox = CheckBox(
            (-210,40,200,30), 
            "Lock Asc/Desc to UPM", 
            callback=self.setUPMLock, 
            value=self.lock2upm, 
            sizeStyle='regular'
            )
        self.w.addGlyphEditorSubview(self.checkbox)
        
        # setting up guides and invisible names... should probably use identifiers
        self.verts = {
            "             "  : [self.f.info.descender, "descender"],
            "            "   : [self.f.info.xHeight,   "xHeight"],
            "           "    : [self.f.info.capHeight, "capHeight"],
            "          "     : [self.f.info.ascender,  "ascender"]
            } 
        
        for vert in self.verts.keys():
            self.f.appendGuideline(position=(0, self.verts[vert][0]), angle=0, name=vert, color=(0,0,0,1))
            
        # saving whether user has guides locked previously
        self.user_lock = getDefault("glyphViewLockGuides")
        setDefault("glyphViewLockGuides", False)
    
    def setUPMLock(self, sender):
        if sender.get() == 0:
            self.lock2upm = False
        else:
            self.lock2upm = True
            self.setMetrics()
        
        setExtensionDefault(self.pref_key, self.lock2upm)

    def becomeInactive(self):
        self.f = CurrentFont()
        
        for guideline in self.f.guidelines:
            if guideline.name in self.verts.keys():
                self.f.removeGuideline(guideline)
                
        setDefault("glyphViewLockGuides", self.user_lock)
        
        self.w.removeGlyphEditorSubview(self.checkbox)
        
    def mouseDown(self, point, clickCount):
        if abs(point.y - self.f.info.descender) < abs(self.f.info.ascender - point.y):
            self.desc_driving = True
        else:
            self.desc_driving = False
    
    def mouseDragged(self, point, delta):
        self.setMetrics()
                
    def mouseUp(self, point):
        self.setMetrics()
                
    def setMetrics(self):
        self.f = CurrentFont()
        
        vert_settings = {}
        for guideline in self.f.guidelines:
            if guideline.name in self.verts.keys():
                if self.desc_driving == True and self.lock2upm == True:
                    if guideline.name == list(self.verts.keys())[3]:
                        guideline.y = self.f.info.descender + self.f.info.unitsPerEm
                elif self.desc_driving == False and self.lock2upm == True:
                    if guideline.name == list(self.verts.keys())[0]:
                        guideline.y = self.f.info.ascender - self.f.info.unitsPerEm
                        
                setattr(self.f.info, self.verts[guideline.name][1], guideline.y) 
            
    def getToolbarTip(self):
        return "Edit Font Dimensions"
        
    def getToolbarIcon(self):
        return(toolbarIcon)
        
installTool(EditFontDimensions())