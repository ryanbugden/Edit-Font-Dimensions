from mojo.events import EditingTool, installTool, addObserver, removeObserver
from mojo.UI import getDefault, setDefault, CurrentGlyphWindow
from mojo.extensions import setExtensionDefault, getExtensionDefault
from AppKit import NSImage
from vanilla import CheckBox
from os import path

dirname = path.dirname(__file__)
toolbarIcon = NSImage.alloc().initByReferencingFile_(path.join(dirname, "../resources/EditFontDimensionsTool_Icon.pdf"))

class EditFontDimensions(EditingTool):
    '''
    RoboFont extension for visually manipulating 
    your font info’s Dimensions values.
    
    Ryan Bugden
    1.2.3 2023.05.31
    1.2.2 2020.04.03
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
        self.asc_driving  = False
        self.xh_driving   = False
        self.ch_driving   = False
        
        # setting up user preferences
        self.pref_key = 'com.ryanbugden.EditFontDimensions'
        
        # adding the UPM lock checkbox
        self.lock2upm = getExtensionDefault(self.pref_key, False)
        self.checkbox = CheckBox(
            (-210,40,200,30), 
            "Lock Asc/Desc to UPM", 
            callback   = self.set_upm_lock, 
            value      = self.lock2upm, 
            sizeStyle  = 'regular'
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
        
        addObserver(self, "close", "fontWillClose")
    

    def set_upm_lock(self, sender):
        if sender.get() == 0:
            self.lock2upm = False
        else:
            self.lock2upm = True
            self.set_metrics()
        
        setExtensionDefault(self.pref_key, self.lock2upm)


    def set_metrics(self):
        self.f = CurrentFont()

        vert_keys = list(self.verts.keys())
        asc_from_desc = self.f.info.descender + self.f.info.unitsPerEm
        desc_from_asc = self.f.info.ascender  - self.f.info.unitsPerEm

        for guideline in self.f.guidelines:
            gd_name = guideline.name

            if self.desc_driving:
                if gd_name == vert_keys[0]:
                    self.f.info.descender = guideline.y
                if self.lock2upm and gd_name == vert_keys[3]:
                    guideline.y = asc_from_desc
                    self.f.info.ascender = guideline.y

            elif self.asc_driving:
                if gd_name == vert_keys[3]:
                    self.f.info.ascender = guideline.y
                if self.lock2upm and gd_name == vert_keys[0]:
                    guideline.y = desc_from_asc
                    self.f.info.descender = guideline.y

            elif self.xh_driving and gd_name == vert_keys[1]:
                self.f.info.xHeight = guideline.y

            elif self.ch_driving and gd_name == vert_keys[2]:
                self.f.info.capHeight = guideline.y



    def clean_up(self, font):
        for guideline in font.guidelines:
            if guideline.name in self.verts.keys():
                font.removeGuideline(guideline)
                
        setDefault("glyphViewLockGuides", self.user_lock)
        
        self.w.removeGlyphEditorSubview(self.checkbox)
        
        removeObserver(self, "fontWillClose")


    def becomeInactive(self):
        self.f = CurrentFont()
        self.clean_up(self.f)
        

    def close(self, notification):
        self.clean_up(notification['font'])
        

    def mouseDown(self, point, clickCount):
        self.verts_and_labels = {
            self.f.info.descender: "descender",
            self.f.info.xHeight:   "xHeight",
            self.f.info.capHeight: "capHeight",
            self.f.info.ascender:  "ascender"
            } 
        self.starting_place = self.verts_and_labels[min(list(self.verts_and_labels.keys()), key=lambda x:abs(x-point.y))]  # Find the closest dimension

        self.desc_driving = (self.starting_place == "descender")
        self.asc_driving  = (self.starting_place == "ascender")
        self.xh_driving   = (self.starting_place == "xHeight")
        self.ch_driving   = (self.starting_place == "capHeight")
    

    def mouseDragged(self, point, delta):
        self.set_metrics()
                

    def mouseUp(self, point):
        self.set_metrics()
                

    def getToolbarTip(self):
        return "Edit Font Dimensions"
        

    def getToolbarIcon(self):
        return(toolbarIcon)
        

installTool(EditFontDimensions())
