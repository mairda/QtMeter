# This Python file uses the following encoding: utf-8
from PySide6.QtCore import (Qt, QLoggingCategory, qCDebug)
from PySide6.QtWidgets import (QColorDialog, QDialog, QGraphicsScene)

from PySide6.QtGui import (QBrush, QColor)

from dlgQtMSettings import Ui_dlgSettings

from qtmTODMath import qtmTODMath

class dlgSettings(QDialog):
    '''
    Settings dialog class for QtMeter application

    dlgSettings class is derived from QDialog and uses a QDialog UI to display
    and modify settings for the QtMeter application.
    '''

    todCalc = qtmTODMath()
    ignoreLatLonChanged = False

    minColor = QColor("green")
    maxColor = QColor("red")
    spectrumColor = QColor("yellow")

    # This is used to prevent recursive signals when we use coupled spinboxes
    # and have to update the other when we update each. The coupling case is
    # to keep the high frequency filter limit above the low frequency filter
    # limit and vice-versa.
    fixingF = False

    logCategory = QLoggingCategory("QtMeter.Dialog.Settings")

    def __init__(self):
        '''
        Constructs a dlgSettings dialog. The dialog UI will be initialized and
        control signals linked to slots.
        '''

        super(dlgSettings, self).__init__()

        # self.load_ui()
        self.ui = Ui_dlgSettings()
        self.ui.setupUi(self)
        self.ui.rbDMS.toggle()
        self.enable_lat_lon_input()
        self.ui.dsbLatFloat.setSingleStep(0.00027778)

        # These don't work in UI design
        alignmentFlag = Qt.AlignRight
        self.ui.sbLatDegrees.setAlignment(alignmentFlag)
        self.ui.sbLatMinutes.setAlignment(alignmentFlag)
        self.ui.sbLatSeconds.setAlignment(alignmentFlag)
        self.ui.dsbLatFloat.setAlignment(alignmentFlag)
        self.ui.sbLonDegrees.setAlignment(alignmentFlag)
        self.ui.sbLonMinutes.setAlignment(alignmentFlag)
        self.ui.sbLonSeconds.setAlignment(alignmentFlag)
        self.ui.dsbLonFloat.setAlignment(alignmentFlag)

        self.connectControls()

    def set_latitude(self, newLat):
        '''
        Preset the values in latitude controls. This is done in floating point
        degrees and the setting of the floating point degrees control causes the
        degrees/minutes/seconds values to be automatically populated.

        Parameters
        ----------
            newLat: Floating point number
                The new latitude to use for the control
        '''

        # Ignore None
        if newLat is not None:
            # Get North or South and only use a positive value
            isNorth = (newLat >= 0.0)
            newLat = abs(newLat)
            if isNorth:
                self.ui.rbLatNorth.setChecked(True)
            else:
                self.ui.rbLatSouth.setChecked(True)

            self.ui.dsbLatFloat.setValue(newLat)

    def set_longitude(self, newLon):
        '''
        Preset the values in longitude controls. This is done in floating point
        degrees and the setting of the floating point degrees control causes the
        degrees/minutes/seconds values to be automatically populated.

        Parameters
        ----------
            newLon: Floating point number
                The new longitude to use for the control
        '''

        # Ignore None
        if newLon is not None:
            # Get East or West and only use a positive value
            isEast = (newLon >= 0.0)
            newLon = abs(newLon)
            if isEast:
                self.ui.rbLonEast.setChecked(True)
            else:
                self.ui.rbLonWest.setChecked(True)

            self.ui.dsbLonFloat.setValue(newLon)

    def set_latlon(self, latlon):
        '''
        Set both latitude and longitude from a tuple containing both
        Parameters
        ----------
            lanlon: a two item tuple containing a numeric latitude and numeric
                    longitude (in that order in the tuple)
        '''

        self.set_latitude(latlon[0])
        self.set_longitude(latlon[1])

    def get_latitude_float(self):
        '''
        Return the current latitude, make negative for Southern hemisphere
        '''

        lat = self.ui.dsbLatFloat.value()
        if self.ui.rbLatSouth.isChecked():
            lat = 0.0 - lat

        return lat

    def get_longitude_float(self):
        '''
        Return the current longitude, make negative for Western hemisphere
        '''

        lon = self.ui.dsbLonFloat.value()
        if self.ui.rbLonWest.isChecked():
            lon = 0.0 - lon

        return lon

    def setup_enabled_lat_lon_controls(self, isDMS):
        '''
        Set which controls are enabled, floating point degrees or degrees
        minutes and seconds

        Parameters
        ----------
            isDMS: Boolean
                True to enable the degrees,  minutes and seconds controls. False
                to enable the floating point degrees controls.
        '''

        self.ui.sbLatDegrees.setEnabled(isDMS)
        self.ui.lblLatDegrees.setEnabled(isDMS)
        self.ui.sbLatMinutes.setEnabled(isDMS)
        self.ui.lblLatMinutes.setEnabled(isDMS)
        self.ui.sbLatSeconds.setEnabled(isDMS)
        self.ui.lblLatSeconds.setEnabled(isDMS)

        self.ui.dsbLatFloat.setEnabled(not isDMS)
        self.ui.lblLatFloat.setEnabled(not isDMS)

        self.ui.sbLonDegrees.setEnabled(isDMS)
        self.ui.lblLonDegrees.setEnabled(isDMS)
        self.ui.sbLonMinutes.setEnabled(isDMS)
        self.ui.lblLonMinutes.setEnabled(isDMS)
        self.ui.sbLonSeconds.setEnabled(isDMS)
        self.ui.lblLonSeconds.setEnabled(isDMS)

        self.ui.dsbLonFloat.setEnabled(not isDMS)
        self.ui.lblLonFloat.setEnabled(not isDMS)

    def enable_lat_lon_input(self):
        '''
        Slot for the input format being changed (degrees or degrees, minutes and
        seconds)
        '''

        self.setup_enabled_lat_lon_controls(self.ui.rbDMS.isChecked())

    def new_lat_float(self, newValue):
        '''
        Slot for the floating point latitude being changed. A modification
        causes the degrees, minutes and second to be adjusted automatically. In
        the same way adjusting degrees, minutes or seconds will cause the
        floating point degrees to be adjusted. Since each results in the other
        being signaled there is a control variable ignoreLatLonChanged used to
        prevent recursive execution.

        Parameters
        ----------
            newValue: floating point number
                The new latitude to use
        '''

        # If we are being adjusted by DMS changes do nothing
        if self.ignoreLatLonChanged:
            return

        # Use it to set the DMS without looping back valueChanged
        self.ignoreLatLonChanged = True

        # debug_message("lat value changed type {}".format(type(newValue)))
        deg = abs(self.todCalc.get_angle_degrees(newValue))
        min = abs(self.todCalc.get_angle_minutes(newValue))
        sec = abs(self.todCalc.get_angle_seconds(newValue))
        # debug_message("\\_ {} == {} {} {}".format(newValue, deg, min, sec))
        self.ui.sbLatDegrees.setValue(deg)
        self.ui.sbLatMinutes.setValue(min)
        self.ui.sbLatSeconds.setValue(sec)

        self.ignoreLatLonChanged = False

    def new_lat_DMS(self, value):
        '''
        Slot for the latitude degrees, minutes or seconds being changed. A
        modification causes the floating point degrees to be adjusted
        automatically. In the same way adjusting floating point degrees will
        cause the degrees, minutes and seconds to be adjusted. Since each
        results in the other being signaled there is a control variable
        ignoreLatLonChanged used to prevent recursive execution.

        This slot is used for all three of degrees, minutes and seconds so the
        value parameter is not used and the values of all three read from the
        controls

        Parameters
        ----------
            value: integer
                The new value
        '''

        # If we are being adjusted by float degrees changes do nothing
        if self.ignoreLatLonChanged:
            return

        # Use them to set the float without looping back valueChanged
        self.ignoreLatLonChanged = True

        # Just get the three of them
        deg = self.ui.sbLatDegrees.value()
        min = self.ui.sbLatMinutes.value()
        sec = self.ui.sbLatSeconds.value()

        # Compute and set the float value
        fDegs = self.todCalc.get_DMS_angle_float(deg, min, sec)
        # fDegs = self.todCalc.getDMSFloat(deg, min, sec)
        self.ui.dsbLatFloat.setValue(fDegs)

        self.ignoreLatLonChanged = False

    def new_lon_float(self, newValue):
        '''
        Slot for the floating point longitude being changed. A modification
        causes the degrees, minutes and second to be adjusted automatically. In
        the same way adjusting degrees, minutes or seconds will cause the
        floating point degrees to be adjusted. Since each results in the other
        being signaled there is a control variable ignoreLatLonChanged used to
        prevent recursive execution.

        Parameters
        ----------
            newValue: floating point number
                The new logitude to use
        '''

        # If we are being adjusted by DMS changes do nothing
        if self.ignoreLatLonChanged:
            return

        # Use it to set the DMS without looping back valueChanged
        self.ignoreLatLonChanged = True

        # debug_message("lat value changed type {}".format(type(newValue)))
        deg = abs(self.todCalc.get_angle_degrees(newValue))
        min = abs(self.todCalc.get_angle_minutes(newValue))
        sec = abs(self.todCalc.get_angle_seconds(newValue))
        # debug_message("\\_ {} == {} {} {}".format(newValue, deg, min, sec))
        self.ui.sbLonDegrees.setValue(deg)
        self.ui.sbLonMinutes.setValue(min)
        self.ui.sbLonSeconds.setValue(sec)

        self.ignoreLatLonChanged = False

    def new_lon_DMS(self, value):
        '''
        Slot for the longitude degrees, minutes or seconds being changed. A
        modification causes the floating point degrees to be adjusted
        automatically. In the same way adjusting floating point degrees will
        cause the degrees, minutes and seconds to be adjusted. Since each
        results in the other being signaled there is a control variable
        ignoreLatLonChanged used to prevent recursive execution.

        This slot is used for all three of degrees, minutes and seconds so the
        value parameter is not used and the values of all three read from the
        controls

        Parameters
        ----------
            value: integer
                The new value
        '''

        # If we are being adjusted by float degrees changes do nothing
        if self.ignoreLatLonChanged:
            return

        # Use them to set the float without looping back valueChanged
        self.ignoreLatLonChanged = True

        # Just get the three of them
        deg = self.ui.sbLonDegrees.value()
        min = self.ui.sbLonMinutes.value()
        sec = self.ui.sbLonSeconds.value()

        # Compute and set the float value
        fDegs = self.todCalc.get_DMS_angle_float(deg, min, sec)
        # fDegs = self.todCalc.getDMSFloat(deg, min, sec)
        self.ui.dsbLonFloat.setValue(fDegs)

        self.ignoreLatLonChanged = False

    def set_spec_color(self, newColor):
        self.spectrumColor = newColor
        view = self.ui.gvSpectrumColor
        scene = view.scene()
        if scene is None:
            scene = QGraphicsScene()
            view.setScene(scene)

        # Fill it with the chosen color
        specBrush = QBrush(self.spectrum_color)
        scene.setBackgroundBrush(specBrush)
        scene.clear()

    @property
    def spectrum_color(self):
        return self.spectrumColor

    def new_spec_color(self):
        newColor = QColorDialog.getColor(self.spectrumColor)
        if newColor.isValid():
            self.setSpectrumColor(newColor)

    def set_max_level_color(self, newColor):
        self.maxColor = newColor
        view = self.ui.gvMaxColor
        scene = view.scene()
        if scene is None:
            scene = QGraphicsScene()
            view.setScene(scene)

        # Fill it with the chosen color
        # scene.setSceneRect(0.0, 0.0, self.usefulWidth, useHeight)
        maxBrush = QBrush(self.maximum_color)
        scene.setBackgroundBrush(maxBrush)
        scene.clear()

    @property
    def maximum_color(self):
        return self.maxColor

    def new_max_color(self):
        newColor = QColorDialog.getColor(self.maxColor)
        if newColor.isValid():
            self.setMaxLevelColor(newColor)

    def set_min_level_color(self, newColor):
        self.minColor = newColor
        view = self.ui.gvMinColor
        scene = view.scene()
        if scene is None:
            scene = QGraphicsScene()
            view.setScene(scene)

        # Fill it with the chosen color
        # scene.setSceneRect(0.0, 0.0, self.usefulWidth, useHeight)
        minBrush = QBrush(self.minimum_color)
        scene.setBackgroundBrush(minBrush)
        scene.clear()

    @property
    def minimum_color(self):
        return self.minColor

    def new_min_color(self):
        newColor = QColorDialog.getColor(self.minColor)
        if newColor.isValid():
            self.setMinLevelColor(newColor)

    def set_colors(self, newColors):
        '''
        Set colors from a tuple containing all of them as text names
        Parameters
        ----------
            newColors: a three item tuple containing text color names for
                       minimum, maximum and spectrum (in that order in the
                       tuple)
        '''

        self.set_min_level_color(QColor.fromString(newColors[0]))
        self.set_max_level_color(QColor.fromString(newColors[1]))
        self.set_spec_color(QColor.fromString(newColors[2]))


    def audio_filter_type_changed(self, newFilter):
        '''
        Handle signal from audio filter type combo box when the filter is
        changed. There are a variety of combinationos of Low/High frequency
        enablements based on the filter type
        Parameters
        ----------
            newFilter: Text name of the newly selected filter
        '''

        # qCDebug(self.logCategory, "Filter changed to {}".format(newFilter))
        if newFilter == "Low pass":
            loOn = False
            hiOn = True
        elif newFilter == "High pass":
            loOn = True
            hiOn = False
        elif newFilter == "Band pass":
            loOn = True
            hiOn = True
        elif newFilter == "Band stop":
            loOn = True
            hiOn = True
        else:
            loOn = True
            hiOn = True

        sUI = self.ui
        sUI.lblLowF.setEnabled(loOn)
        sUI.sbLowF.setEnabled(loOn)
        sUI.lblHighF.setEnabled(hiOn)
        sUI.sbHighF.setEnabled(hiOn)

    def toggle_audio_filter(self, checked):
        '''
        Handle signal from audio filter group box when it is toggled
        Parameters
        ----------
            checked: True when the state changes to checked, False when
                     unchecked
        '''

        if checked is True:
            self.audio_filter_type_changed(self.ui.cbFilterType.currentText)

    @property
    def audio_filter_enabled(self):
        return self.ui.gbAudioFilter.isChecked()

    def audio_filter_exists(self, filterName):
        return (self.ui.cbFilterType.findText(filterName) != -1)

    @property
    def audio_filter_type(self):
        if self.audio_filter_enabled:
            txt = self.ui.cbFilterType.currentText()
        else:
            # No audio filter enabled
            txt = ""
        return txt

    @property
    def audio_filter_low_frequency(self):
        if self.ui.sbLowF.isEnabled:
            fLim = self.ui.sbLowF.value()
        else:
            # Not used for the current filter type
            fLim = -1

        return fLim

    @property
    def audio_filter_high_frequency(self):
        if self.ui.sbHighF.isEnabled:
            fLim =  self.ui.sbHighF.value()
        else:
            # Not used for the current filter type
            fLim = -1

        return fLim

    @property
    def audio_filter_order(self):
        if self.ui.sbOrder.isEnabled:
            filtOrder = self.ui.sbOrder.value()
        else:
            # Not enabled (default of order 3)
            filtOrder = 3

        return filtOrder

    def disable_audio_filter(self):
        self.ui.gbAudioFilter.setChecked(False)

    def enable_audio_filter(self):
        self.ui.gbAudioFilter.setChecked(True)

    def set_audio_filter_type(self, newFilter):
        '''
        Change the currently selected audio filter if newFilter is the text of
        an item in the combobox
        Parameters
        ----------
            newFilter: String name of the new filter to select
        '''

        newIndex = self.ui.cbFilterType.findText(newFilter)
        if newIndex != -1:
            self.ui.cbFilterType.setCurrentIndex(newIndex)

    def set_audio_filter_low_f(self, newFreq):
        '''
        Set the audio filter low frequency to newFreq
        '''

        self.ui.sbLowF.setValue(newFreq)

    def set_audio_filter_high_f(self, newFreq):
        '''
        Set the audio filter high frequency to newFreq
        '''

        self.ui.sbHighF.setValue(newFreq)

    def set_audio_filter_order(self, newOrder):
        '''
        Set the filter order, higher values have more steep roll-off, for
        editing current range is limited to 1 through 99
        '''

        if newOrder < 1:
            newOrder = 1
        elif newOrder > 99:
            newOrder = 99

        # Just in-case, use int() when setting the control
        self.ui.sbOrder.setValue(int(newOrder))

    def audio_filter_low_f_changed(self, newFreq):
        '''
        The audio filter low frequency changed, keep the high frequency above it
        Parameters
        ----------
            newFreq: New low frequency selection
        '''

        if self.fixingF is False:
            if self.ui.sbHighF.value() <= newFreq:
                # Prevent recursive calling and make the change
                self.fixingF = True
                self.ui.sbHighF.setValue(newFreq + 1)
        else:
            self.fixingF = False

    def audio_filter_high_f_changed(self, newFreq):
        '''
        The audio filter high frequency changed, keep the high frequency below
        it
        Parameters
        ----------
            newFreq: New low frequency selection
        '''

        if self.fixingF is False:
            if self.ui.sbLowF.value() >= newFreq:
                # Prevent recursive calling
                self.fixingF = True
                self.ui.sbHighF.setValue(newFreq - 1)
        else:
            self.fixingF = False

    @property
    def audio_windowing_enabled(self):
        return self.ui.gbWindowing.isChecked()

    def window_function_exists(self, fnName):
        return (self.ui.cbWindowFn.findText(fnName) != -1)

    @property
    def window_function_type(self):
        if self.audio_windowing_enabled:
            txt = self.ui.cbWindowFn.currentText()
        else:
            # No audio filter enabled
            txt = ""
        return txt

    def set_window_function_type(self, newType):
        '''
        Change the currently selected window function if newType is the text of
        an item in the combobox
        Parameters
        ----------
            newType: String name of the new window function to select
        '''

        newIndex = self.ui.cbWindowFn.findText(newType)
        if newIndex != -1:
            self.ui.cbWindowFn.setCurrentIndex(newIndex)

    def disable_window_function(self):
        self.ui.gbWindowing.setChecked(False)

    def enable_window_function(self):
        self.ui.gbWindowing.setChecked(True)

    @property
    def use_fast_view_updates(self):
        fastUpdates = self.ui.cbFastViewUpdates.isChecked()
        return fastUpdates

    def disable_fast_view_updates(self):
        self.ui.cbFastViewUpdates.setChecked(False)

    def enable_fast_view_updates(self):
        self.ui.cbFastViewUpdates.setChecked(True)

    def connectControls(self):
        '''
        Connect Qt signals with slots
        '''

        # Shorten the length of the references to the ui object to reduce some
        # line lengths
        sUI = self.ui

        sUI.rbDMS.toggled.connect(self.enable_lat_lon_input)

        sUI.dsbLatFloat.valueChanged.connect(self.new_lat_float)
        sUI.sbLatDegrees.valueChanged.connect(self.new_lat_DMS)
        sUI.sbLatMinutes.valueChanged.connect(self.new_lat_DMS)
        sUI.sbLatSeconds.valueChanged.connect(self.new_lat_DMS)

        sUI.dsbLonFloat.valueChanged.connect(self.new_lon_float)
        sUI.sbLonDegrees.valueChanged.connect(self.new_lon_DMS)
        sUI.sbLonMinutes.valueChanged.connect(self.new_lon_DMS)
        sUI.sbLonSeconds.valueChanged.connect(self.new_lon_DMS)

        sUI.pbChangeMinColor.clicked.connect(self.new_min_color)
        sUI.pbChangeMaxColor.clicked.connect(self.new_max_color)
        sUI.pbChangeSpecColor.clicked.connect(self.new_spec_color)

        sUI.gbAudioFilter.toggled.connect(self.toggle_audio_filter)
        sUI.cbFilterType.currentTextChanged.connect(self.audio_filter_type_changed)
        sUI.sbLowF.valueChanged.connect(self.audio_filter_low_f_changed)
        sUI.sbHighF.valueChanged.connect(self.audio_filter_high_f_changed)
