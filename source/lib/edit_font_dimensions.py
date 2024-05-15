from mojo.events import EditingTool, installTool, addObserver, removeObserver
from mojo.UI import getDefault, setDefault, AllGlyphWindows, inDarkMode
from mojo.extensions import setExtensionDefault, getExtensionDefault
from AppKit import NSImage
from vanilla import CheckBox
from os import path


dirname = path.dirname(__file__)
TOOLBAR_ICON = NSImage.alloc().initByReferencingFile_(path.join(dirname, "../resources/toolbar_icon.pdf"))
SPECIAL_GUIDE_COLORS = (
            (0.01,0.012,0.013, 1),
            (0.99,0.998,0.9998,1),
        )
EXTENSION_KEY = 'com.ryanbugden.editFontDimensions'

DEBUG = False


class EditFontDimensions(EditingTool):
    

    def setup(self):
        self.f = CurrentFont()
        self.all_fonts_guides = {}
        self.driving_guideline = None


    def becomeActive(self):
        self.f = CurrentFont()
        self.last_snap_driving = "descender"

        # Adding the UPM lock checkbox
        self.snap_to_upm = getExtensionDefault(EXTENSION_KEY, False)
        self.add_checkboxes()

        # Pre-cleaning guides
        identifiers = getExtensionDefault(EXTENSION_KEY + ".identifiers", [])
        for f in AllFonts():
            for guideline in f.guidelines:
                if guideline.identifier in identifiers:
                    f.removeGuideline(guideline)
                    identifiers.remove(guideline.identifier)
        setExtensionDefault(EXTENSION_KEY + ".identifiers", identifiers)
    
        # Setting up heights and guides
        self.update_dimension_info()
        self.set_up_guides()
        
        # Saving whether user has guides locked previously
        self.user_lock = getDefault("glyphViewLockGuides")
        setDefault("glyphViewLockGuides", False)
        
        addObserver(self, "font_will_close", "fontWillClose")
        addObserver(self, "font_did_close", "fontDidClose")
        addObserver(self, "font_did_open", "fontDidOpen")
        addObserver(self, "glyph_window_did_open", "glyphWindowDidOpen")
        addObserver(self, "did_undo", "didUndo")
    

    def checkbox_callback(self, sender):
        self.snap_to_upm = sender.get()
        for w, checkbox in self.checkboxes:
            if not checkbox == sender:
                checkbox.set(self.snap_to_upm)
        if self.snap_to_upm:
            self.set_metrics()

        setExtensionDefault(EXTENSION_KEY, self.snap_to_upm)


    def update_dimension_info(self):
        self.f = CurrentFont()
        self.dimensions = ["ascender", "capHeight", "xHeight", "descender"]
        self.dim_values_and_names = {}
        for attribute in self.dimensions:
            self.dim_values_and_names[getattr(self.f.info, attribute)] = attribute


    def set_up_guides(self):
        guide_color = SPECIAL_GUIDE_COLORS[0]
        if inDarkMode():
            guide_color = SPECIAL_GUIDE_COLORS[1]
        self.remove_all_guides()
        self.all_fonts_guides = {}
        identifiers = getExtensionDefault(EXTENSION_KEY + ".identifiers", [])
        for f in AllFonts():
            font_guides = {}
            for attribute in self.dimensions:
                new_guide = f.appendGuideline(position=(0, getattr(f.info, attribute)), angle=0, name=None, color=guide_color)
                font_guides[attribute] = new_guide
                identifiers.append(new_guide.identifier)
            self.all_fonts_guides[f] = font_guides
        setExtensionDefault(EXTENSION_KEY + ".identifiers", identifiers)


    def set_metrics(self):
        if not self.driving_guideline in self.f.guidelines:
            return

        # Change the height of whatever you're moving.
        setattr(self.f.info, self.driving_attr, self.driving_guideline.y)

        if self.snap_to_upm:
            if not self.f in self.all_fonts_guides.keys():
                return
            # Change the ascender if the descender was the last to drive, and you’re locking to UPM
            if self.last_snap_driving == "descender":
                guideline = self.all_fonts_guides[self.f]["ascender"]
                asc_from_desc = self.f.info.descender + self.f.info.unitsPerEm
                guideline.y = asc_from_desc
                self.f.info.ascender = asc_from_desc

            # Change the descender if the ascender was the last to drive, and you’re locking to UPM
            elif self.last_snap_driving == "ascender":
                guideline = self.all_fonts_guides[self.f]["descender"]
                desc_from_asc = self.f.info.ascender - self.f.info.unitsPerEm
                guideline.y = desc_from_asc
                self.f.info.descender = desc_from_asc


    def remove_all_guides(self):
        # Note: do we need this anymore?
        for f, font_guides in self.all_fonts_guides.items():
            for guideline in font_guides.values():
                if f:
                    try:
                        f.removeGuideline(guideline)
                    except:
                        continue
        for f in AllFonts():
            for guideline in f.guidelines:
                if guideline.color in SPECIAL_GUIDE_COLORS:
                    f.removeGuideline(guideline)


    def becomeInactive(self):
        self.remove_all_guides()
        self.remove_checkboxes()
        removeObserver(self, "fontWillClose")
        removeObserver(self, "fontDidClose")
        removeObserver(self, "fontDidOpen")
        removeObserver(self, "glyphWindowDidOpen")
        # Restore user’s preference for whether guidelines are locked.
        setDefault("glyphViewLockGuides", self.user_lock)


    def add_checkboxes(self):
        self.checkboxes = []
        for w in AllGlyphWindows():
            checkbox_width = 190
            checkbox_height = 50
            padding = 8
            checkbox = CheckBox(
                (-checkbox_width - padding, padding, -padding, checkbox_height), 
                "Snap Asc–Desc to UPM", 
                callback   = self.checkbox_callback, 
                value      = self.snap_to_upm, 
                sizeStyle  = 'regular'
                )
            w.addGlyphEditorSubview(checkbox, identifier='com.ryanbugden.editFontDimensions.snapToUPMCheckbox', clear=True)
            self.checkboxes.append((w, checkbox))


    def remove_checkboxes(self):
        for w, checkbox in self.checkboxes:
            w.removeGlyphEditorSubview(checkbox)
        self.checkboxes = []
        

    def font_will_close(self, notification):
        f = notification['font']
        self.remove_all_guides()
        if f in self.all_fonts_guides.keys():
            self.all_fonts_guides.pop(f)
        

    def font_did_close(self, notification):
        self.set_up_guides()


    def font_did_open(self, font):
        self.remove_all_guides()
        self.set_up_guides()


    def glyph_window_did_open(self, window):
        self.remove_all_guides()
        self.set_up_guides()
        self.remove_checkboxes()
        self.add_checkboxes()


    def mouseDown(self, point, clickCount):
        self.update_dimension_info()
        # Find the closest dimension to the mouse pointer, and designate a driver (guideline)
        if DEBUG: print("mouse-down")
        self.driving_attr, self.driving_guideline = min(self.all_fonts_guides[self.f].items(), key=lambda x: abs(point.y - x[1].y))
        if self.driving_attr in ["ascender", "descender"]:
            self.last_snap_driving = self.driving_attr
        if DEBUG: print(self.driving_attr, self.f, self.driving_guideline in self.f.guidelines)
    

    def mouseDragged(self, point, delta):
        self.set_metrics()
                

    def mouseUp(self, point):
        self.set_metrics()


    def did_undo(self, notification):
        self.set_metrics()
                

    def getToolbarTip(self):
        return "Edit Font Dimensions"


    def getToolbarIcon(self):
        return(TOOLBAR_ICON)
        


installTool(EditFontDimensions())
