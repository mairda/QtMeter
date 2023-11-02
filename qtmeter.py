# This Python file uses the following encoding: utf-8
#
# QtMeter is an extremely basic example of an audio level meter as a Qt
# application in Python. The development used python3.10 and PySide 6.3. It also
# uses the following python libraries:
# pyaudio, numpy, math
#
# Note that no reference audio level is available unless you know the value to
# add in your own case so the apparent dB level displayed by the meter is NOT a
# SPL and is only a self-relative dB value. However, it is a couple of thousand
# lines of python reading audio sample data and displaying a tunable level meter
# for recorded sample data.
#
# It uses a thread to receive audio samples and keeps a rolling moving average
# of the amplitude. The duration of the rolling average can be tuned using the
# "Sample Window" control. The level is displayed using a QProgressBar control
# with the value changed on the events of a main window QTimer object with a
# tick frequency that can be set using the "Meter Frame Rate" in the main
# window.
#
# The backround of the rolling average level attempts to draw horizontal color
# gradients to represent the time-of-day horizontally at a user specified
# latitude/longitude. Use the Settings button to set the earth position. Each
# average level is plotted at the expected position in that day view when it was
# recorded. The view shows a 24 hour period, when the audio level lines reach 24
# hours long older data is discarded and the background shifts left to make
# space for each new record plotted.
#
# An absolute minimum and maximum of the mean level is kept until you reset it
# with the button at the top right of the "Absolute (dB)" group box. If the
# minimum or maxium exceeds the limits of the level meter then it is reset.
#
# The updates to and access to thread data are synchronized with a single
# QRecursiveMutex object for all thread state requiring synchronized access.
#
# You can configure the audio sampling configuration but the controls are
# populated with standard values so any sound device that doesn't support chosen
# sampling settings will not operate when the Start button is pushed. Equally,
# any sampling settings a device supports that are not shown in the UI will not
# be usable to monitor audio.
#
# The audio device used will be the default audio device on the system and may
# be changed using audio management software on the system to use different
# sources.
#
# QtMeter is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# QtMeter is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# QtMeter. If not, see <https://www.gnu.org/licenses/>.
#
import sys
import time

import numpy

import math

import pyaudio

from PySide6.QtCore import (Qt, QCoreApplication, QLoggingCategory,
                            QRecursiveMutex, QSettings, qSetMessagePattern,
                            QTimer, QThread, qCDebug, qCWarning, Slot)
# from PySide6.QtDataVisualization import Q3DTheme
from PySide6.QtWidgets import (QApplication, QDialog, QGraphicsScene,
                               QGraphicsView, QMessageBox)
from PySide6.QtGui import (QColor, QIcon, QLinearGradient, QPen)

from dlgQtMeter import Ui_QtMeter

from qtmSettings import dlgSettings

from qtmTODMath import qtmTODMath

from qtmAudioRxThread import qtmAudioRxThread

# import timeit


# FIXME: If possible it would be good to find ways to reduce memory usage. The
#        application isn't big when running but after a day of tracking a sound
#        source at 32kHz, 16-bit, mono it needs about a constant 3.5MB.

class QtMeter(QDialog):
    '''
    Main Window class for QtMeter application

    QtMeter class is derived from QDialog and uses a QDialog UI to display and
    modify configuration for the QtMeter application.
    '''

    # High speed timing of meter updates
    # tLast = 0.0
    # nMeterSets = 0
    # sumMeterSetDurations = 0.0

    updateTimer = QTimer()
    tPeriod = 0
    ignoreUpdateTimer = False;
    audioThread = None

    # For debugging, set this to True to increase the update rate of the day
    # view rolling signal and spectrum views
    # debugDayUpdates = True
    debugDayUpdates = False

    # Debugging FFT views
    # Power ratio
    debugFFTView = 0
    # dB ratio
    # debugFFTView = 1
    # Normalized 0..1
    # debugFFTView = 2
    # Normalized standard deviation of 1
    debugFFTView = 3
    maxFFTBinVal = 0

    fftMinDetail = 0.5

    lastdB = 0.0
    reflexdBs = []
    maxReflexdBs = 16

    changingPeriod = False
    changingHz = False

    # Both views have the same width
    usefulWidth = 0

    # Each horizontal pixel represents passage of time
    tXPixel = 0

    # ...and we have to re-draw based on a background move when the view is
    # full
    tXSlide = 0

    # This is for the level view
    usefulHeight = 0

    # The spectrum view has a different height
    specUsefulHeight = 0

    # Time amount in seconds to slide the whole day meters when they are filled
    filledDayMetersSlide = 3.0 * 60.0 * 60.0
    forceNewBackground = False

    # Colors for the skyview backdrop to the level and frequency meters
    cSkyDayNightJoin = QColor.fromRgb(0x00, 0x61, 0x7b)
    # cSkyNoon = QColor.fromRgb(0x87, 0xce, 0xfb)
    cSkyNoon = QColor.fromRgb(0x4F, 0x99, 0xfb)
    cSkyMidnight = QColor("black")
    # cSkyTransPeak = QColor.fromRgb(0x9f, 0x5c, 0x6b)
    cSkyTransPeak = QColor.fromRgb(0xca, 0x69, 0x1e)

    # Data for the level meter
    minHistory = []
    nMinHistory = 0
    maxHistory = []
    nMaxHistory = 0
    tAudioStart = -1.0
    tHistory = []
    ntHistory = 0
    absMin = 0.0
    absMax = -90.0
    minRoll = 0.0
    maxRoll = -90.0
    preMaxRoll = 0.0
    preMinRoll = 0.0
    minLimit = 0.0
    maxLimit = 0.0
    meterRange = 0.0
    xRatio = 1.0
    yRatio = 1.0
    # historyCount = 240
    minColor = QColor("green")
    minPen = None
    maxColor = QColor("red")
    maxPen = None

    # Data for the spectrum meter (tHistory is shared with the level meter)
    # FIXME: Make selection of the (maximum) spectrum alpha a user choice in
    #        the settings dialog
    scrollSpectrum = False
    fHistory = []
    nfHistory = 0
    fScaling = []
    nfScaling = 0
    fMutex = QRecursiveMutex()
    fdBMin = -360.0
    spectrumColor = QColor("yellow")
    # spectrumAlphaLimit = 0.5
    spectrumAlphaLimit = 0.75
    # spectrumAlphaLimit = 0.9
    # spectrumAlphaLimit = 3.5  # (0.7)
    # spectrumAlphaLimit = 4.5  # (0.9)
    # spectrumAlphaLimit = 1.00
    nyquistFrequency = 0
    iLastDrawn = -1

    # If this is True the spectrum image is based on dB power per-frequency, if
    # this is False the spectrum is based on simple power level per-frequency
    spectrumIndB = False

    # Window to be applied to the samples for the spectrum view
    windowFn = "Blackman-Harris"

    # Filter settings to be applied to spectrum view
    audioFilterName = ""
    audioFilterLowF = 0
    audioFilterHighF = 22050
    audioFilterOrder = 3

    handlingBadFilter = False

    # Some counters for timesteps (the time when a new item is added to the
    # display). These are used to reduce what gets done when checking for a
    # timestep being reached.
    timeStepChecks = 0
    timeSteps = 0
    timeStepMeanChecks = 0.0
    timeStepLastStep = 0
    timeStepNextCheck = 0

    todCalc = qtmTODMath()
    latitude = 0
    longitude = 0

    # Seconds in a day, we can do conversions from angles to seconds or back
    kDaySeconds = 24.0 * 60.0 * 60.0

    # Transits are sunrise/sunset when the sun crosses the horizon and the day
    # scene needs an orange/red coloring.
    # Use trans for symbol names about them to reduce line lengths a little

    # Limit the time width we draw the color to a half hour around the actual
    # transit
    # kSunTransSeconds = 30.0 * 60.0


    # Use one of the definitions of twilight obtained from NOAA at:
    # https://www.weather.gov/fsd/twilight
    # The largest gives the best space for a color gradient to show
    kCivilTwilight = kDaySeconds * 6.0 / 360.0
    kNauticalTwilight = kDaySeconds * 12.0 / 360.0
    kAstronomicalTwilight = kDaySeconds * 18.0 / 360.0

    # FIXME: Make selection of this a user choice in the settings dialog
    kPrePostTransSeconds = kAstronomicalTwilight

    # Total transition time
    kSunTransSeconds = 2.0 * kPrePostTransSeconds

    # Show (or not) debug data when drawing the day view
    debugDrawDay = False
    # debugDrawDay = True

    # Persistent state key constants version, latitude, longitude, user colors,
    # spectrum view style
    kStateVersion = "StateVersion"
    kLatitude = "Latitude"
    kLongitude = "Longitude"
    kMinColor = "Color-Minimum-Signal"
    kMaxColor = "Color-Maximum-Signal"
    kSpecColor = "Color-Spectrum"
    kSpectrumIndB = "Spectrum-View-dB"

    kWindowType = "Audio-Window-Function"

    kFilterType = "Audio-Filter-Type"
    kFilterLowF = "Audio-Filter-Low-F"
    kFilterHighF = "Audio-Filter-High-F"
    kFilterOrder = "Audio-Filter-Order"

    currentStateVersion = "1.1.0"
    currentStateMaj = 1
    currentStateMid = 1
    currentStateMin = 0

    kThemeIconA = "audio-input-microphone"
    kThemeIconB = "audio-input-microphone-symbolic"
    kThemeIconC = "org.gnome.Settings-microphone-symbolic"

    logCategory = QLoggingCategory("QtMeter")

    def __init__(self, parent=None):
        '''
        Constructs a QtMeter dialog. The dialog UI will be initialized and a
        suitable default icon set, if available. Sets application attributes
        and loads any available persistent settings. Sets limits used by the
        long-term (historical) audio-level meter in the UI. A QTimer is created
        for regular audio level meter update but will be stopped until
        monitoring is configured and started via a UI button click. Needed UI
        control signals will be linked to class member slots.

        Parameters
        ----------
            parent: window object
                A parent window object for this dialog window, or None if it is
                the application main window
        '''

        super(QtMeter, self).__init__()

        # self.todCalc.doDBug = True
        # aTime = self.todCalc.get_time_now()
        # debug_message("Time now: {}".format(aTime))
        # self.todCalc.test_function(aTime)

        # self.load_ui()
        self.ui = Ui_QtMeter()
        self.ui.setupUi(self)

        # Use a theme icon for a microphone as the application icon
        if QIcon.hasThemeIcon(self.kThemeIconA):
            myIcon = QIcon.fromTheme(self.kThemeIconA)
        elif QIcon.hasThemeIcon(self.kThemeIconB):
            myIcon = QIcon.fromTheme(self.kThemeIconB)
        elif QIcon.hasThemeIcon(self.kThemeIconC):
            myIcon = QIcon.fromTheme(self.kThemeIconC)
        else:
            # Don't change the default application icon because we can't find an
            # icon that we recognize as useful
            myIcon = None

        if myIcon is not None:
            self.setWindowIcon(myIcon)

        # Setup enough information for a default QSettings to work
        QCoreApplication.setOrganizationName("DaveWasHere")
        QCoreApplication.setOrganizationDomain("mair-family.org")
        QCoreApplication.setApplicationName("QtMeter")

        # Set limits that will be used by the timer and not change
        self.__set_history_limits()

        # Load our saved configuration settings
        self.load_persistent_settings()

        # Timer to show meter updates, use what's in the UI
        self.updateTimer.setTimerType(Qt.PreciseTimer)
        self.__set_meter_update_period()
        self.updateTimer.stop()

        self.connect_controls()

    def __enable_audio_controls(self, enable=True):
        '''
        Enable or disable the audio sampling configuration controls in the UI
        based on the enable argument.

        Parameters
        ----------
            enable: bool
                True (default): Enable the audio sampling controls
                False: Disable the audio sampling controls
        '''

        self.ui.cbSampleHz.setEnabled(enable)
        self.ui.cbSampleSize.setEnabled(enable)
        self.ui.rbMono.setEnabled(enable)
        self.ui.rbStereo.setEnabled(enable)

    def toggle_meter(self, checked):
        '''
        Start or stop audio sampling. Used as a slot for a UI control that
        can supply a checked state.

        If an audio sampling thread exists it and meter updates are stopped. If
        an audio sampling thread does not exist one is created, configured based
        on UI sampling controls and started. In each case some UI items are
        modified. For example, the text in the button is changed to "Stop" when
        audio monitoring is started and changed to "Start" when audio monitoring
        is stopped. The first draw of the background for the sample data history
        is drawn when audio monitoring is started.

        Parameters
        ----------
            checked: bool
                Indicates the checked state supplied when called by a Qt signal.
                However, checked is unused in this function.
        '''

        if self.audioThread is None:
            # Start when not listening
            self.audioThread = qtmAudioRxThread()
            self.audioThread.setObjectName("QtMeter Audio Monitor")
            # Use UI values to set the chunk bytes
            self.audioThread.set_sample_window(self.ui.dsbSampleWindow.value())
            # FIXME: This should include space for channels
            srn = self.get_sample_rate_number()
            ssize = self.__get_sample_bytes()
            buffSize = srn * ssize / self.ui.sbFramesPerSecond.value()
            self.audioThread.set_sample_frame_byte_len(buffSize)
            self.audioThread.set_sample_rate(srn)
            self.audioThread.set_sample_size(self.__get_sample_code())
            # self.audioThread.set_FFT_sample_duration(self.tXPixel)
            if self.ui.rbStereo:
                self.audioThread.set_stereo_source()
            else:
                # Assume mono if not stereo
                self.audioThread.set_mono_source()
            #  DWH self.audioThread.enable_normalized_FFT()

            # Set the time we use for a single FFT view item (a column in the
            # FFT day view
            colTime = int(86400.0 / (self.ui.gvSpecHistory.width() - 2))
            self.audioThread.set_fft_view_duration(colTime)

            # Set any window settings
            wfn = self.windowFn
            self.audioThread.set_window_type(wfn)

            # Set any filter settings
            filtName = self.audioFilterName
            filtLowF = self.audioFilterLowF
            filtHighF = self.audioFilterHighF
            filtOrder = self.audioFilterOrder
            self.audioThread.set_filter_type(filtName)
            self.audioThread.set_filter_low_f(filtLowF)
            self.audioThread.set_filter_high_f(filtHighF)
            self.audioThread.set_filter_order(filtOrder)

            # Connect the bad filter message back to ourselves
            self.audioThread.showBadFilterMessage.connect(self.showBadFilterMessage)

            # Don't use now as the start time, use the first record we make, so
            # just create empty histories
            self.tHistory = []
            self.ntHistory = 0
            self.minHistory = []
            self.nMinHistory = 0
            self.maxHistory = []
            self.nMaxHistory = 0
            self.fMutex.lock()
            self.fHistory = []
            self.nfHistory = 0
            self.fScaling = []
            self.nfScaling = 0
            self.fMutex.unlock()

            # Draw empty views
            view = self.findChild(QGraphicsView, "gvHistory")
            self.__draw_history_background(view)

            view = self.findChild(QGraphicsView, "gvSpecHistory")
            self.__draw_history_background(view, isLevel=False)

            # We can't change audio device settings while capturing so disable
            # the controls for it
            self.__enable_audio_controls(False)

            self.audioThread.start()
            self.tAudioStart = time.time()
            self.changed_update_period(self.ui.dsbUpdatePeriod.value())

            # Make enough space for many common maximum frequency values for the
            # spectrum view and setup so that they look right relative to the
            # related graphics view for the spectrum when aligned.
            gvRect = self.ui.gvSpecHistory.geometry()
            oldMaxFRect = self.ui.lblSpecMaxF.geometry()
            fNyquist = self.get_sample_rate_number() / 2000.0
            fNyquistText = "{} k".format(fNyquist)
            self.ui.lblSpecMaxF.setText(fNyquistText)
            if fNyquist == 22.05:
                msg = "44.1kHz Nyquist rectangle "
                msg += "is {}".format(self.ui.lblSpecMaxF.geometry())
                qCDebug(self.logCategory, msg)
                # debug_message("44.1kHz Nyquist rectangle is {}".format(self.ui.lblSpecMaxF.geometry()))
            self.ui.lblSpecMaxF.setGeometry(10, oldMaxFRect.y(),
                                            gvRect.left() - 19,
                                            oldMaxFRect.height())

            # This alignment doesn't persist when using the ui editor in Qt
            # creator so set it here
            self.ui.lblSpecMaxF.setAlignment(Qt.AlignmentFlag.AlignRight)

            # debug_message("New sample rate number {}/{}".format(maxF, maxFText))
            # debug_message("Old max F label: {}".format(oldMaxFRect))
            # debug_message("Moved location: {}".format(self.ui.lblSpecMaxF.geometry()))

            # Start the update timer and change the Start button to be a Stop
            # button
            self.updateTimer.start()
            self.ui.pbStartStop.setText("Stop")
            tTip = "Click to stop the meter and stop sampling audio"
            self.ui.pbStartStop.setToolTip(tTip)
        else:
            # Stop when listening
            self.updateTimer.stop()
            self.tAudioStart = -1.0
            self.audioThread.end_meter()
            self.audioThread.deleteLater()
            self.audioThread = None

            # When stopped we can choose new audio sample settings
            self.__enable_audio_controls(True)

            # Stop button becomes a Start button
            self.ui.pbStartStop.setText("Start")
            tTip = "Click to start sampling audio and updating the meter"
            self.ui.pbStartStop.setToolTip(tTip)

            # Yield to allow background objects like the audio thread to end
            QThread.sleep(1)

    @Slot(str)
    def showBadFilterMessage(self, msg):
        '''
        Slot for signal from audio thread when filtering produces out-of-range
        data, usually when the filter has a cutoff frequency too close to the
        band edge for the sampling
        '''

        # Ignore repeats
        if self.handlingBadFilter:
            return

        self.handlingBadFilter = True

        QMessageBox.warning(self, "Filtering error", msg)

        if self.audioThread is not None:
            self.toggle_meter(False)

        # Allow repeats again
        self.handlingBadFilter = False

    def damp_reducing_dB_value(self, dBValue):
        '''
        Given a dBValue, damp descreases in it based on data history.

        Parameters
        ----------
            dBValue: Number
                New dB value to consider damping

        Returns a number that's a replacement for dBValue that's been damped if
        it was decreasing.
        '''

        # Only damp value decreasing from last recorded
        if (dBValue < self.lastdB):
            # Number of consecutive decreasing items we have noted, and an extra
            # one for the count of dB values we'll process
            reflexCount = len(self.reflexdBs)
            dbCount = reflexCount + 1

            # Number of the record being processed, plus a summed denominator
            # to re-scale summed dBValues into the original range
            nDownCount = dbCount
            nDenom = nDownCount

            # Summed new dbValue (multiply by the record number, new value has
            # highest priority, oldest and highest number has lowest priority)
            # dampdB = dBValue * nDownCount
            dampdB = dBValue

            # Walk through all the recorded decreasing dBValues
            iCount = 0
            for adBVal in self.reflexdBs:
                # Update the record being worked on and keep a denominator based
                # on it
                iCount += 1
                # nDownCount -= 1.0
                # nDenom += 1.0 / (nDownCount / 2.0)
                nDenom += iCount

                # Add the current record to the dB sum
                # dampdB += adBVal / (nDownCount / 2.0)
                # dampdB += adBVal * iCount
                dampdB += adBVal

            # If the record count plus the new one would exceed the maximum,
            # remove an entry
            if reflexCount >= self.maxReflexdBs:
                self.reflexdBs.pop(0)
            # Add the new record to the history
            self.reflexdBs.append(dBValue)

            # Get an integer dBValue based on the tracked sum and denominator
            # newdBVal = dampdB / nDenom
            newdBVal = dampdB / (iCount + 1.0)

            # Show cases approaching the low limit
            if newdBVal < -80.0:
                msg = "Damping meter from {:.2f} ".format(dBValue)
                msg += "to {:.1f} ".format(newdBVal)
                msg += "using {:.2f}/{:.2f} ".format(dampdB, nDenom)
                msg += "in {} records".format(dbCount)
                qCDebug(self.logCategory, msg)
                # debug_message("Damping meter from {:.2f} to {:.1f} using {:.2f}/{:.2f} in {} records".format(dBValue, newdBVal, dampdB, nDenom, dbCount))
        else:
            # New value does not represent a decreasing dB, so drop history and
            # use new value as-is
            self.reflexdBs.clear()
            newdBVal = dBValue

        return newdBVal

    def changed_sample_window(self, sampleWindow):
        '''
        Slot for a changed sample window control value. If there is an audio
        monitoring thread notify it of the change.

        The purpose of the sample window is to have an average that exceeds the
        frame rate but isn't too long. It should prevent the meter display being
        extremely sensitive if higher than the update period. Automatic value
        when set will be 1.5 times the meter update period.

        Parameters
        ----------
            sampleWindow: floating point
                The new sample window (in seconds) to use
        '''

        # Only need to tell a listening thread that the value has changed
        if self.audioThread is not None:
            self.audioThread.set_sample_window(sampleWindow)

    def changed_auto_window(self, newState):
        '''
        Slot for changed state of the checkbox to choose the sample window
        automatically. Calls the slot used when the update period for the meter
        is changed in order to actually set the sample window period.

        Parameters
        ----------
            newState: Boolean
                Indicates if the checkbox was set (True) or cleared (False)
        '''

        # Let the update period do the work (makes a change only if we checked
        # the automatic window control, no change if we unchecked it)
        self.changingPeriod = True
        updatePeriod = self.ui.dsbUpdatePeriod.value()
        self.changed_update_period(updatePeriod)
        self.changingPeriod = False

    def __set_meter_update_period(self):
        '''
        Use UI control with the meter refresh period to set the period of the
        QTimer used to automatically refresh the meter.
        '''

        msTimer = int(1000.0 * self.ui.dsbUpdatePeriod.value())
        self.updateTimer.setInterval(msTimer)

    def changed_update_period(self, newUpdatePeriod):
        '''
        Slot for changed value of the meter refresh period. If automatic choice
        of the sample window is enabled it will compute a new window period. It
        will stop any active QTimer, change the period and if there is an audio
        monitoring thread the QTimer will be restarted. The meter refresh rate
        can be changed via the refresh period or the refresh frequency. A change
        to one requires changing the other. Only one is the source of the change
        made but each can change the value of the other. To prevent recursive
        calling of the slots the real source of the change has a boolean class
        member it uses to indicate it is changing the other. For an actual
        change to the update period control self.changingPeriod is set True
        before changing the update frequency control to the new value and reset
        to false after changing the update frequency. If this is called due to
        a change made as a result of a changed refresh frequency then
        self.changingHz will be true and this function will exit before trying
        to change the frequency control.

        Parameters
        ----------
            newUpdatePeriod: floating point
                The new update period in seconds to be used
        '''

        if self.ui.cbAutoWindow.isChecked():
            # Use 1.5 times the update period as the sample window
            newWindow = round(1.5 * newUpdatePeriod, 3)
            self.ui.dsbSampleWindow.setValue(newWindow)

        self.updateTimer.stop()
        # The UI shouldn't let the following happen, but it should be in
        # probably be in __set_meter_update_period anyway
        # timerPeriod = round(newUpdatePeriod * 1000.0)
        # if timerPeriod < 1:
        #     timerPeriod = 1
        # elif timerPeriod > 1000:
        #     timerPeriod = 1000
        # self.updateTimer.setInterval(timerPeriod)
        self.__set_meter_update_period()
        if self.audioThread is not None:
            self.updateTimer.start()

        if self.changingHz:
            # Prevent recursive changing
            return

        self.changingPeriod = True
        newHz = round(1.0 / newUpdatePeriod)
        self.ui.sbFramesPerSecond.setValue(newHz)
        self.changingPeriod = False

    def change_update_Hz(self, newUpdateHz):
        '''
        Slot for changed value of the meter refresh rate. Actual changes to
        class and state is only made in the slot for a changed update period so
        this slot computes a new peiod from the new rate and sets the value of
        the refresh period control. The meter refresh rate can be changed via
        the refresh period or the refresh frequency. A change to one requires
        changing the other. Only one is the source of the change made but each
        can change the value of the other. To prevent recursive calling of the
        slots the real source of the change has a boolean class member it uses
        to indicate it is changing the other. For an actual change to the update
        rate control self.changingHzis set True before setting the update period
        control to the new value and reset to false after that change completes.
        If this is called due to a change made as a result of a changed refresh
        period then self.changingPeriod will be true and this function will exit
        before trying to change the period control.

        Parameters
        ----------
            newUpdateHz: integer
                The new update frequency in Herts to be used
        '''

        if self.changingPeriod:
            # Prevent recursive changing
            return

        self.changingHz = True
        if newUpdateHz > 0:
            updatePeriod = round(1.0 / newUpdateHz, 3)
            self.ui.dsbUpdatePeriod.setValue(updatePeriod)
        self.changingHz = False

    def get_sample_rate_text(self):
        '''
        Get the currently displayed text in the audio sample rate control

        Returns a string containing the displayed value in the control
        '''

        rateText = self.ui.cbSampleHz.currentText()
        if rateText == "":
            # Default to 44100Hz
            rateText = "44100"

        return rateText

    def get_sample_rate_number(self):
        '''
        Get the currently displayed text in the audio sample rate control as
        an integer.

        Returns the selected audio sample rate as an integer
        '''
        srt = self.get_sample_rate_text()
        return int(srt)

    def __get_sample_code(self):
        '''
        Get the pyaudio sample size code for the selected value in the audio
        sample size control.

        Returns a pyaudio pa* code for the selected audio sample size and
        defaults to pyaudio.paInt16
        '''

        sizeText = self.ui.cbSampleSize.currentText()
        if sizeText == "16-bit":
            sizeCode = pyaudio.paInt16
        elif sizeText == "32-bit":
            sizeCode = pyaudio.paInt32
        elif sizeText == "32-bit Float":
            sizeCode = pyaudio.paFloat32
        elif sizeText == "24-bit":
            sizeCode = pyaudio.paInt24
        elif sizeText == "8-bit":
            sizeCode = pyaudio.paInt8
        else:
            # Default to 16-bit signed int
            sizeCode = pyaudio.paInt16

        return sizeCode

    def __get_sample_bytes(self):
        sizeText = self.ui.cbSampleSize.currentText()
        if sizeText == "8-bit":
            sizeBytes = 1
        elif sizeText == "16-bit":
            sizeBytes = 2
        elif sizeText == "24-bit":
            sizeBytes = 3
        elif sizeText == "32-bit":
            sizeBytes = 4
        elif sizeText == "32-bit Float":
            sizeBytes = 4
        else:
            # Default to 16-bit signed int
            sizeBytes = 2

        return sizeBytes

    def __get_channels(self):
        if self.ui.rbStereo:
            channels = 2
        else:
            # Not stereo is mono
            channels = 1

        return channels

    def is_sample_format_supported(self):
        '''
        Take the current audio sampling control values and use them to check if
        they make a sampling configuration supported by the default audio
        device.
        '''

        rateNum = self.get_sample_rate_number()
        sampleType = self.__get_sample_code()
        channels = self.__get_channels()

        audioDev = pyaudio.PyAudio()
        try:
            defDev = audioDev.get_default_host_api_info()
        except IOError:
            defDev = None
        if defDev != None:
            devID = defDev['defaultInputDevice']
        else:
            devID = 0
        try:
            fmtOk = audioDev.is_format_supported(rateNum,
                                                 input_device=devID,
                                                 input_channels=channels,
                                                 input_format=sampleType)
        except ValueError:
            fmtOk = False

        return fmtOk

    def changed_sample_Hz(self, newIndex):
        '''
        Slot for signal when a new value is selected in the audio sample rate
        control.

        parameters
        ----------
            newIndex: int
                The index of the newly selected item in the audio sample rate
                QComboBox

        Ignores an attempt to change the sample rate while audio sampling is
        already active.

        If the sample rate can be changed it is verified (with other audio
        sampling settings) as a supported sample format for the current device
        and a message box displayed if not.
        '''

        # No point in changing it if the audio thread is running already
        if self.audioThread is not None:
            mBox = QMessageBox()
            msg = "You can't change the audio sample rate when the meter is "
            msg += "active"
            mBox.setText(msg)
            msg = "Stop the meter, change the audio sample rate and Start the "
            msg += "meter again"
            mBox.setInformativeText(msg)
            mBox.setStandardButtons(QMessageBox.Ok)
            mBox.exec()
        else:
            fmtOk = self.is_sample_format_supported()
            rateText = self.get_sample_rate_text()

            if not fmtOk:
                mBox = QMessageBox()
                msg = "Unsupported standard "
                msg += "sample rate {}Hz, try another".format(rateText)
                mBox.setText(msg)
                msg = "The selected common sample rate is not supported by the "
                msg += "default input device, choose another rate or change "
                msg += "the default device in your desktop configuration"
                mBox.setInformativeText(msg)
                mBox.setStandardButtons(QMessageBox.Ok)
                mBox.exec()

    def changed_sample_size(self, newIndex):
        '''
        Slot for signal when a new value is selected in the audio sample size
        control.

        parameters
        ----------
            newIndex: int
                The index of the newly selected item in the audio sample size
                QComboBox

        Ignores an attempt to change the sample size while audio sampling is
        already active.

        If the sample size can be changed it is verified (with other audio
        sampling settings) as a supported sample format for the current device
        and a message box displayed if not.
        '''

        # No point in changing it if the audio thread is running already
        if self.audioThread is not None:
            mBox = QMessageBox()
            msg = "You can't change the audio sample size when the meter is "
            msg += "active"
            mBox.setText(msg)
            msg = "Stop the meter, change the audio sample size and Start the "
            msg += "meter again"
            mBox.setInformativeText(msg)
            mBox.setStandardButtons(QMessageBox.Ok)
            mBox.exec()
        else:
            fmtOk = self.is_sample_format_supported()
            sizeText = self.ui.cbSampleSize.currentText()

            if not fmtOk:
                mBox = QMessageBox()
                msg = "Unsupported standard "
                msg += "sample size {}, try another".format(sizeText)
                mBox.setText(msg)
                msg = "The selected common sample size is not supported by the "
                msg += "default input device, choose another rate or change "
                msg += "the default device in your desktop configuration"
                mBox.setInformativeText(msg)
                mBox.setStandardButtons(QMessageBox.Ok)
                mBox.exec()

    def __get_history_scene(self, view):
        '''
        Get the QGraphicsScene from a QGraphicsView or, if none exists, create
        one.

        Parameters
        ----------
            view: QGraphicsView
                The QGraphicsView to get a QGraphicsScene for

        Returns
        -------
            The instance of the GQraphicsView's QGraphicsScene.
        '''

        # If it has no scene, add one
        scene = view.scene()
        if scene is None:
            scene = QGraphicsScene()
            view.setScene(scene)

        return scene

    def __offset_day_part_by_time(self, pLeft, pRight, sceneWidth):
        '''
        Given the width of a scene to draw in from a left to right co-ordinate,
        offset the left and right values by a fraction of the width that is
        equal to the timestamp of the class history data's first record in local
        time as a fraction of a 24 hour day. Correct it for any known daylight
        savings time.

        This is used to draw the background of the dialog's QGraphicsView as a
        synthesized light view representing the whole day as it is at the
        latitude/longitde location selected in the application settings.

        parameters
        ----------
            pLeft: number
                Zero based left position that will be drawn from.
            pRight: number
                Zero based right position that will be drawn to
            width: number
                Width of the control to be drawn in

            pLeft and pRight are assumed to be as-if zero is midnight and width
            is assumed to be the maximum right value to be drawn at and
            represents the position where a pRight represents the last draw time
            before midnight of the next day.

        Returns
        -------
            A tuple containing a new (pLeft, pRight) where the values have been
            shifted by a fraction of width equal to the timestamp in seconds of
            the first audio level history record as a fraction of 24 hours in
            seconds.

        Errors
        ------
            Raises OverFlowError if there are no audio level history timestamps
            Raises OverFlowError if the timestamp in seconds as a fraction of 24
            hours in seconds is less than zero or greater than one.
            Returns (None, None) if pLeft or pRight is None
        '''

        if pLeft is None or pRight is None:
            return (None, None)

        # Get a time now in case we don't have time history but need to know
        # if there is DST
        tForDST = time.localtime()
        try:
            # Get the start time as a fraction into the 24-hour day
            if self.ntHistory > 0:
                tLoc = time.localtime(self.tHistory[0])
                correctDST = (tLoc.tm_isdst == 1)
                startSec = tLoc.tm_hour * 3600.0\
                            + tLoc.tm_min * 60.0\
                            + tLoc.tm_sec
                startFrac = startSec / (self.kDaySeconds)
            else:
                correctDST = (tForDST.tm_isdst == 1)
                raise OverflowError

            if (startFrac < 0.0) or (startFrac > 1.0):
                raise OverflowError

        except OverflowError:
            # Only show the warning if we are not capturing audio. This function
            # should only be called if we are capturing audio but we might have
            # just started and have no time history yet, that's okay
            if self.audioThread is None:
                msg = "Unable to calculate start time as day fraction, using now"
                qCWarning(self.logCategory, msg)

            startFrac = self.todCalc.get_time_now_fraction_of_day()
            correctDST = (tForDST.tm_isdst == 1)

        if correctDST is True:
            startFrac += -3600.0 / self.kDaySeconds
            if startFrac < 0.0:
                startFrac += 1.0

        # Fraction of the day that start is in pixels across sceneWidth
        startPixels = startFrac * sceneWidth

        # Re-position left and right based on the start time
        pLeft -= startPixels
        pRight -= startPixels

        # If both are negative then re-position it to the right by the scene
        # width
        if (pLeft < 0) and (pRight < 0):
            pLeft += sceneWidth
            pRight += sceneWidth

        # When returning the leftmost element of the day it's left will usually
        # be negative and right will be positive. The caller has to deal with it
        # because it means splitting the display and putting all the positive
        # positions at the start of the scene and all the negative positions
        # (time in this day before we started recording) at the right of the
        # scene
        return (pLeft, pRight)

    def __get_color_at_X(self, width, cLeft, cRight, x):
        '''
        Given the scene width, left and right horizontal linear gradient colors
        and an X position, return the expected QColor at that position.

        Doesn't do hypotenuse (x, y) gradients, only horizontal (x). It only
        works using the integer component colors

        Parameters
        ----------
            width: number
                The horizontal width containing a linear color gradient
            cLeft: QColor
                The color at the left of width
            cRight: QColor
                The color at the right of width
            x: number
                The horizontal position within width to compute the color
                between cLeft and cRight

        Returns
        -------
            QColor that would be the color at position x on a linear gradient as
            wide as width and with left color cLeft and right color cRight
        '''

        if self.debugDrawDay:
            msg = "Get color at {} in {} wide gradient".format(x, width)
            qCDebug(self.logCategory, msg)
            # debug_message("Get color at {} in {} wide gradient".format(x, width))
            rL = cLeft.red()
            gL = cLeft.green()
            bL = cLeft.blue()
            rR = cRight.red()
            gR = cRight.green()
            bR = cRight.blue()
            lL = cLeft.lightness()
            lR = cRight.lightness()
            msg = "Color range is ({},{},{}) to ({},{},{})".format(rL, gL, bL,
                                                                   rR, gR, bR)
            qCDebug(self.logCategory, msg)
            if lL > lR:
                msg = "Left is lighter than right getting color at gradient "
                msg += "position"
                qCDebug(self.logCategory, msg)
            elif lR > lL:
                msg = "Right is lighter than left getting color at gradient "
                msg += "position"
                qCDebug(self.logCategory, msg)
            else:
                msg = "Left and right have same lightness getting color at "
                msg += "gradient position"
                qCDebug(self.logCategory, msg)
        if x > width:
            msg = "Attempt to get color at {} beyond ".format(x)
            msg += "gradient width {}".format(width)
            qCWarning(self.logCategory, msg)
        xRatio = (1.0 * x) / (1.0 * width)
        tmpRed = int(cLeft.red() + xRatio * (cRight.red() - cLeft.red()))
        tmpGreen = int(cLeft.green() + xRatio * (cRight.green() - cLeft.green()))
        tmpBlue = int(cLeft.blue() + xRatio * (cRight.blue() - cLeft.blue()))
        # tmpRed = int(xRatio * cLeft.red() + (1.0 - xRatio) * cRight.red())
        # tmpGreen = int(xRatio * cLeft.green() + (1.0 - xRatio) * cRight.green())
        # tmpBlue = int(xRatio * cLeft.blue() + (1.0 - xRatio) * cRight.blue())

        if self.debugDrawDay:
            msg = "Got color ({},{},{})".format(tmpRed, tmpGreen, tmpBlue)
            qCDebug(self.logCategory, msg)

        return QColor.fromRgb(tmpRed, tmpGreen, tmpBlue)

    def __get_quart_X_limits(self, qNum, width):
        '''
        Assuming a day has four sky light gradients, midnight to dawn; dawn to
        noon; noon to sunset and sunset to midnight and given an integer to
        represent one of these, obtain the left and right horizontal position of
        that quart within a space that is as wide as width.

        Uses the latitude/longitude to compute the correct zero based positions
        for these on the current day assuming current time is midnight.

        Use the term "quart" to indicate any of these periods of the day even
        though their durations are rarely an exact quarter of a day.

        Parameters
        ----------
            qNum: integer
                The quart to obtain the left and right position of, values are
                0, 1, 2, 3 representing the "quart" ordered starting at midnight
                to dawn and ending at sunset to midnight on the same day.
            width: number
                The width of the space in which the quart is to be drawn

        Returns
        -------
            A tuple containing (xLeft, xRight) as the limits of the range of
            space within width that would represent the identified quart.
        '''

        # Get the fractions of the day that are night and day
        daytimeFrac = self.todCalc.daytime_fraction_of_day()
        nighttimeFrac = self.todCalc.nighttime_fraction_of_day()

        # Use the scene rectangle to get the size of a quart
        wholeNightWidth = nighttimeFrac * width
        halfNightWidth = wholeNightWidth / 2.0
        wholeDayWidth = daytimeFrac * width
        halfDayWidth = wholeDayWidth / 2.0

        if qNum == 0:
            # Midnight to sunrise
            xLeft = 0.0
            xRight = halfNightWidth - 1.0
        elif qNum == 1:
            # Sunrise to midday
            xLeft = halfNightWidth
            xRight = halfNightWidth + halfDayWidth - 1.0
        elif qNum == 2:
            # Midday to sunset
            xLeft = halfNightWidth + halfDayWidth
            xRight = halfNightWidth + wholeDayWidth - 1.0
        elif qNum == 3:
            # Sunset to midnight
            xLeft = halfNightWidth + wholeDayWidth
            xRight = wholeNightWidth + wholeDayWidth

        if self.debugDrawDay is True:
            msg = "Quart X limits for quart {}".format(qNum)
            qCDebug(self.logCategory, msg)
            msg = "  X range {} to {}".format(xLeft, xRight)
            qCDebug(self.logCategory, msg)

        return (xLeft, xRight)

    def __get_trans_X_limits(self, qNum, width, xQLeft, xQRight):
        '''
        Assuming a day has two transits of the sun across the horizon that occur
        at down and sunset which are each the boundaries between two different
        sky light gradients: midnight to dawn joining dawn to noon; and noon to
        sunset joining sunset to midnight then given the identity of one of the
        four sky gradients ("quarts") obtain a left and right horizonal position
        a considered the part of the solar transition in that quart, within a
        space that is as wide as width.

        These are used to draw a dawn and sunset area in an orange/red color on
        the skylight background drawn in the QGraphicsView used to show the long
        term audio level view.

        Uses a class member with a constant time in seconds for the width of the
        whole transition, half of which occurs in each sky light gradient
        meaning there are four parts of transitions where each is in one of the
        day quarts.

        There is a half transit at the left edge of the dawn to noon and sunset
        to midnight quarts and there is a half transit at the right edge of the
        midight to dawn and sunset to midnight quarts.

        Caller supplies which quart, left and right edge of the quart and the
        width of the view being used to draw the quarts and transits.

        Parameters
        ----------
            qNum: integer
                The quart to obtain the left and right position of the transit
                in, values are 0, 1, 2, 3 representing the "quart" ordered
                starting at midnight to dawn and ending at sunset to midnight on
                the same day.
            width: number
                The width of the whole view in which the transit is to be drawn
            xQLeft: number
                The left horizontal position in-use for the quart qNum
            qXRight: number
                The right horizontal position in-use for the quart qNum

        Returns
        -------
            A tuple containing (xTransLeft, xTransRight) as the limits of the
            range of space within width that would represent the half transit
            in the identified quart.
        '''

        # Get the size of the time either side of the set/rise as a fraction
        # of the day and amount of scene width
        halfTransFrac = self.kPrePostTransSeconds / (24.0 * 3600.0)
        halfTransWidth = halfTransFrac * width

        # Midnight to sunrise and midday to sunset
        if (qNum == 0) or (qNum == 2):
            # Transit part is on the right edge of what we'll draw
            xTransLeft = xQRight - halfTransWidth
            if xTransLeft < xQLeft:
                xTransLeft = xQLeft
            xTransRight = xQRight
        # Sunrise to midday and sunset to midnight
        elif (qNum == 1) or (qNum == 3):
            # Transit part is on the left edge of what we'll draw
            xTransLeft = xQLeft
            xTransRight = xQLeft + halfTransWidth
            if xTransRight > xQRight:
                xTransRight = xQRight

        if self.debugDrawDay is True:
            msg = "Transit X limits for quart {} ""in {} width".format(qNum,
                                                                       width)
            qCDebug(self.logCategory, msg)
            msg = "  Quart X range {} to {}".format(xQLeft, xQRight)
            qCDebug(self.logCategory, msg)
            msg = "  Trans X range {} to {}".format(xTransLeft, xTransRight)
            qCDebug(self.logCategory, msg)

        return (xTransLeft, xTransRight)

    def __draw_day_rect(self, scene, xLeft, xRight, yHeight, cLeft, cRight,
                        id=""):
        '''
        Draw a simulated skylight gradient rectangle in the QGraphicsScene of
        the dialog's QGraphicsView.

        The gradient is linear in the horizontal direction. Vertically there is
        no variable material.

        Parameters
        ----------
            scene: QGraphicsScene
                The scene to draw the rectangle within
            xLeft: number
                The left horizontal position limit of the rectangle within the
                scene
            xRight: number
                The right horizontal position limit of the rectangle within the
                scene
            yHeight: number
                The vertical height of the rectangle to draw within the scene
            cLeft: QColor
                The left color of the sky light gradient to use for the
                rectangle
            cRight: QColor
                The right color of the sky light gradient to use for the
                rectangle
            id: string
                A text label that will be used in the description of the
                rectangle being drawn (if class member debugDrawDay is set True)
        '''

        # Gradient for the primary rectangle being considered
        qGrad = QLinearGradient(xLeft, 0.0, xRight, 0.0)
        qGrad.setColorAt(0.0, cLeft)
        qGrad.setColorAt(1.0, cRight)

        # Create a pen using the gradient
        qPen = QPen(qGrad,
                    1,
                    Qt.SolidLine,
                    Qt.SquareCap,
                    Qt.BevelJoin)

        # Draw the day part as a rectangle
        # Show some debug if enabled
        if self.debugDrawDay is True:
            rL = cLeft.red()
            gL = cLeft.green()
            bL = cLeft.blue()
            rR = cRight.red()
            gR = cRight.green()
            bR = cRight.blue()
            msg = "Drawing {}".format(id)
            msg += " from {} to {}".format(xLeft, xRight)
            msg += " in ({},{},{}) to ({},{},{})".format(rL, gL, bL, rR, gR, bR)
            qCDebug(self.logCategory, msg)
        scene.addRect(xLeft, 0.0, xRight - xLeft, yHeight, qPen, qGrad)

    def draw_sky_quart(self, qNum, scene):
        '''
        Draw a "quart" of the sky light progress within the dialog's
        QGraphicsView.

        Uses the current day of the year to choose size of night and day.

        Obtains reference positions for each quart in the scne assuming it's
        midnight. Then re-positions the quart based on the current time-of-day
        so that the view appears aligned with time

        Include a programmed dawn/sunset transit in an orange red color

        Contains the color definitions for the edge of each element.

        Handles the case of drawing the current quart and the current transit
        when the present time is within it and it has to be split and part is
        drawn on the left of the scene and the other part on the right of the
        scene.

        Parameters
        ----------
            qNum: integer
                The quart being drawn. Consecutively, 0 through 3 where 0
                indicates midnight to dawn and 3 indicates sunset to midnight.
            scene: QGraphicsScene
                The scene for the QGraphicsView the quart is being drawn in.
        '''

        if (qNum < 0) or (qNum > 3):
            raise ValueError

        # Use to turn on/off drawing of all, odd quart or even quart transits,
        # set all three to true to draw all
        drawTrans = True
        drawOddTrans = True
        drawEvenTrans = True

        # Use the scene rectangle to get the size of a quart
        rect = scene.sceneRect()

        # xTransLeft = None
        # xTransRight = None

        # With what we have, the day starting at midnight is:
        # Dark getting brighter: halfNightWidth - sideRiseSetWidth
        # Sunrise still night: sideRiseSetWidth
        # Rising in day: sideRiseSetWidth
        # Day getting brighter: halfDayWidth - sideRiseSetWidth
        # Day getting darker: halfDayWidth - sideRiseSetWidth
        # Setting still day: sideRiseSetWidth
        # Setting in night: sideRiseSetWidth
        # Night getting darker: halfNightWidth - sideRiseSetWidth

        # Current position is a point in the range of the whole set and defines
        # what should be drawn at the horizontal edges of the scene. Each quart
        # has two gradients, it's native and the part of it that is in rise/set

        # Uses some class based colors in multiple places without needing to
        # edit the color values in multiple places. For noon CSDevs uses:
        # defaultSky = QColor.fromRgb(0x57, 0x81, 0xf4)

        # Use the quart to choose left and right colors. Previously used colors
        # that were repeatedly created on drawing are commented but left to show
        # values used
        if qNum == 0:
            # Midnight to sunrise
            cLeft = self.cSkyMidnight
            # cRight = QColor.fromRgb(0xff, 0xbc, 0x8b)
            #  cRight = QColor.fromRgb(0x8f, 0x6c, 0x6b)
            cRight = self.cSkyDayNightJoin
        elif qNum == 1:
            # Sunrise to midday
            # cLeft = QColor.fromRgb(0xff, 0xbc, 0x8b)
            #  cLeft = QColor.fromRgb(0x9f, 0x5c, 0x6b)
            cLeft = self.cSkyDayNightJoin
            # cRight = QColor.fromRgb(0x57, 0x81, 0xf4)
            #  cRight = QColor.fromRgb(0x87, 0xCE, 0xEB)
            #   cRight = QColor.fromRgb(0x87, 0xCE, 0xEB)
            cRight = self.cSkyNoon
        elif qNum == 2:
            # Midday to sunset
            #  cLeft = QColor.fromRgb(0x3c, 0x81, 0xf4)
            #   cLeft = QColor.fromRgb(0x87, 0xce, 0xeb)
            cLeft = self.cSkyNoon
            # cLeft = QColor.fromRgb(0x57, 0x81, 0xf4)
            # cRight = QColor.fromRgb(0xff, 0xbc, 0x8b)
            #  cRight = QColor.fromRgb(0x9f, 0x5c, 0x6b)
            cRight = self.cSkyDayNightJoin
        elif qNum == 3:
            # Sunset to midnight
            # cLeft = QColor.fromRgb(0xff, 0xbc, 0x8b)
            # cLeft = QColor.fromRgb(0x9f, 0x5c, 0x6b)
            cLeft = self.cSkyDayNightJoin
            cRight = self.cSkyMidnight

        # Location of the quart
        xLeft, xRight = self.__get_quart_X_limits(qNum, rect.width())
        xQWidth = xRight - xLeft

        # ...and location of the transit within the quart, if we are drawing it
        xTransLeft = None
        xTransRight = None
        if drawTrans is True:
            if ((drawOddTrans is True) and (qNum % 2 == 1)) or\
                    ((drawEvenTrans is True) and (qNum % 2 == 0)):
                xTransLeft, xTransRight = self.__get_trans_X_limits(qNum,
                                                                    rect.width(),
                                                                    xLeft,
                                                                    xRight)
                xTransWidth = xTransRight - xTransLeft

        # Debug draw material, enable for debug
        if self.debugDrawDay is True:
            rL = cLeft.red()
            gL = cLeft.green()
            bL = cLeft.blue()
            rR = cRight.red()
            gR = cRight.green()
            bR = cRight.blue()
            msg = "Midnight centered quart from {} to {}".format(xLeft, xRight)
            msg += " in ({},{},{}) to ({},{},{})".format(rL, gL, bL, rR, gR, bR)
            qCDebug(self.logCategory, msg)
            if xTransLeft is not None:
                msg = "Midnight centered transit from {}".format(xTransLeft)
                msg += " to {}".format(xTransRight)
                qCDebug(self.logCategory, msg)

        # Re-position the current items based on the start time in the 24-hour
        # day
        xLeft, xRight = self.__offset_day_part_by_time(xLeft, xRight,
                                                       rect.width())
        xTransLeft, xTransRight = self.__offset_day_part_by_time(xTransLeft,
                                                                 xTransRight,
                                                                 rect.width())

        # If we have a transit, we have to get colors before we split any quart
        # that contains the current time. This is so that we calculate the
        # color where we cross between transit and quart based on the whole
        # quart range rather than one of the two parts that exist when we split
        # the quart
        if xTransLeft is not None:
            # Pick the position to call the edge based on the quart
            if (qNum == 0) or (qNum == 2):
                xEdge = xQWidth - xTransWidth
            else:
                xEdge = xTransWidth
            if self.debugDrawDay is True:
                qCDebug(self.logCategory, "Quart width is {}".format(xQWidth))
                msg = "Transit width is {}".format(xTransWidth)
                qCDebug(self.logCategory, msg)
                qCDebug(self.logCategory, "Transit edge is {}".format(xEdge))
            transEdgeColor = self.__get_color_at_X(xQWidth, cLeft, cRight,
                                                   xEdge)
            if (qNum == 0) or (qNum == 2):
                cTransLeft = transEdgeColor
                cTransRight = self.cSkyTransPeak
            else:
                cTransLeft = self.cSkyTransPeak
                cTransRight = transEdgeColor

            # If the start time is within the transit
            if (xTransLeft < 0) and (xTransRight >= 0):
                # Color where we cross from one rectangle to another
                cTransLostRight = self.__get_color_at_X(xTransWidth,
                                                        cTransLeft, cTransRight,
                                                        0 - xTransLeft)

                # New position and left color for right part of transit
                xTransLostLeft = xTransLeft + rect.width()
                xTransLostRight = rect.width() - 1.0
                cTransLostLeft = cTransLeft

                # New gradient for right part of transit
                tmpTransGrad = QLinearGradient(xTransLostLeft, 0.0,
                                               xTransLostRight, 0.0)
                tmpTransGrad.setColorAt(0.0, cTransLeft)
                tmpTransGrad.setColorAt(1.0, cTransLostRight)

                # Take part of the transit for the left in the scene from
                # current zero in the scene. xTransLeft is negative and should
                # be zero, but right is in the correct place. Changing
                # xTransLeft to zero will reduce the width by the amount that's
                # less than zero.
                xTransLeft = 0.0

                # Short gradient for the left side of the view
                cTransLeft = cTransLostRight
            else:
                xTransLostLeft = None
                xTransLostRight = None
                cTransLostLeft = None
                cTransLostRight = None
                tmpTransGrad = None

        # If left is negative and right is positive we are drawing the quart
        # containing the start time so the negative part needs to be on the
        # right of the scene and the positive part starts the scene. This means
        # drawing two rectangles with their own gradients based on the end
        # colors calculated for a continuous quart
        if (xLeft < 0) and (xRight >= 0):
            # Color where we cross from one rectangle to another. It's a
            # horizontal gradient only so we don't need to interpolate the
            # hypotenuse.
            cLostRight = self.__get_color_at_X(xQWidth, cLeft, cRight,
                                               0 - xLeft)

            # New position for right part of quart
            xLostLeft = xLeft + rect.width()
            xLostRight = rect.width() - 1.0
            cLostLeft = cLeft

            # Color where we cross from one rectangle to another. It's a
            # horizontal gradient only so we don't need to interpolate the
            # hypotenuse.
            # cLostRight = self.__get_color_at_X(xLostRight - xLostLeft,
            #                                    cLostLeft, cRight, 0 - xLeft)

            # Take part of the quart for the left in the scene from current zero
            # in the scene. xLeft is negative and should be zero, but right is
            # in the correct place. Changing xLeft to zero will reduce the
            # width by the amount that's less than zero.
            xLeft = 0.0

            # Short gradient for the left side of the view
            cLeft = cLostRight
        else:
            # No quart split required
            xLostLeft = None
            xLostRight = None
            cLostLeft = None
            cLostRight = None

        # Draw the background sky quart
        self.__draw_day_rect(scene, xLeft, xRight, rect.height(), cLeft, cRight,
                             "quart")
        # If we have the start time within the quart we are drawing it has
        # two rectangles, one at each horizontal end of the scene. This draws
        # the one at the right extreme of the scene.
        if xLostLeft is not None:
            self.__draw_day_rect(scene, xLostLeft, xLostRight,
                                 rect.height(), cLostLeft, cLostRight,
                                 "lost left quart")

        # If we are drawing a transit on this quart
        if xTransLeft is not None:
            self.__draw_day_rect(scene, xTransLeft, xTransRight, rect.height(),
                                 cTransLeft, cTransRight, "transit")

            # If we have the start time within the transit we are drawing it has
            # two rectangles, one at each horizontal end of the scene. This
            # draws the one at the right extreme of the scene.
            if xTransLostLeft is not None:
                self.__draw_day_rect(scene, xTransLostLeft, xTransLostRight,
                                     rect.height(), cTransLostLeft,
                                     cTransLostRight, "lost left transit")

    def __limit_data_point(self, pointVal, viewHeight):
        '''
        Limit a point value between zero and the view height minus 1.

        Parameters
        ----------
            pointVal: number
                The point to be kept within limits (if limiting is needed)
            viewHeight: number
                The vertical height to keep the pointVal under. The valid range
                is from zero to viewHeight minus one.

        Returns
        -------
            The pointVal (limited if needed)
        '''

        if pointVal < 0.0:
            pointVal = 0.0
        if pointVal > (viewHeight - 1.0):
            pointVal = viewHeight - 1.0

        return pointVal

    def __draw_history_background(self, view, isLevel=True):
        '''
        Draw the background for the QGraphicsView that will contain the long
        term history of audio sample data.

        The "long term" is one day.

        Parameters
        ----------
            view: QGraphicsView
                The control to draw the history background in
        '''

        if view is not None:
            scene = self.__get_history_scene(view)

            # Use the whole scene and clear it
            if isLevel:
                useHeight = self.usefulHeight
            else:
                useHeight = self.specUsefulHeight

            scene.setSceneRect(0.0, 0.0, self.usefulWidth, useHeight)
            # msg = "Clearing day "
            # if isLevel is True:
            #     msg += "signal level "
            # else:
            #     msg += "spectrum "
            # msg += "background and drawing a new background"
            # qCDebug(self.logCategory, msg)
            scene.clear()

            # Draw linear gradients to roughly represent day and night and
            # include a constant sunset/sunrise duration
            self.draw_sky_quart(0, scene)
            self.draw_sky_quart(1, scene)
            self.draw_sky_quart(2, scene)
            self.draw_sky_quart(3, scene)

            # This draws a grid, enable for position debug
            if self.debugDrawDay is True:
                colorTenTag = QColor("white")
                rect = scene.sceneRect()
                qPen = QPen(colorTenTag,
                            1,
                            # Qt.SolidLine,
                            Qt.DotLine,
                            Qt.SquareCap,
                            Qt.BevelJoin)

                # This drew 10 lines to represent time of day, it makes
                # more sense to use a 12th or 24th of the width
                hourGap = rect.width() / 24.0
                nextHour = -1.0
                lastX = int(rect.width()) - 1
                for x in range(0, lastX):
                    # if x % 10 == 0:
                    if x > nextHour:
                        useX = rect.left() + x
                        scene.addLine(useX, 0.0, useX, 25.0, qPen)
                        nextHour = x + hourGap

    def __set_update_period(self):
        '''
        Set the timestep used as the upate period, the preferred approach is the
        time-period multiplied by the number of horizontal pixels in the
        day-views of signal and spectrum is equal to one day, i.e. the view
        background shows the time-of-day the signal or spectrum was recorded.
        However, there are times when it is useful to run faster to see updates
        take place, that is controlled in the settings dialog's spectrum tab.
        '''

        if self.debugDayUpdates is False:
            # We'll draw up to a whole day of audio level history so find out the
            # number of seconds represented by each useful pixel horizontally
            # self.tPeriod = self.kDaySeconds / self.historyCount
            self.tPeriod = self.kDaySeconds / self.usefulWidth
        else:
            # For debugging, have a faster updating but not daytime related
            # graphics view of the audio level over time
            self.tPeriod = 2

    def __set_history_limits(self):
        '''
        Setup as class members some commonly used values that don't change much
        while running.
        '''

        view = self.findChild(QGraphicsView, "gvHistory")
        if view is not None:
            # Get the size of the view and the frame width (doubled because it
            # surrounds the view so horizontally or vertically the frame line
            # appears twice)
            vSize = view.size()
            frameWidth = 2.0 * view.frameWidth()

            # Calculate the usable width and height for drawing
            self.usefulWidth = vSize.width() - frameWidth
            self.usefulHeight = vSize.height() - frameWidth

            # Calculate the time in seconds represented by a horizontal pixel
            self.tXPixel = 86400.0 / self.usefulWidth

        view = self.findChild(QGraphicsView, "gvSpecHistory")
        if view is not None:
            vSize = view.size()
            frameWidth = 2.0 * view.frameWidth()
            self.specUsefulHeight = vSize.height() - frameWidth
            # qCDebug(self.logCategory, "Set spectrum useful height to {} from {} - {}".format(self.specUsefulHeight, vSize.height(), frameWidth))

        self.__set_update_period()

        # Use the min/max values of the live meter as the vertical range for the
        # audio level we'll show over time
        self.minLimit = 1.0 * self.ui.dBMeter.minimum()
        self.maxLimit = 1.0 * self.ui.dBMeter.maximum()
        self.meterRange = self.maxLimit - self.minLimit

        # The audio level change represented by a single vertical pixel
        self.xRatio = 1.0
        self.yRatio = self.usefulHeight / self.meterRange

    def apply_limit_range(self, aVal):
        '''
        Given a value that is assumed to be an audio sample level in dB, limit
        it to the range between the minimum and maximum limit members of the
        class instance. These are set based on the minimum/maximum values of the
        audio level control in the UI.
        '''
        if aVal > self.maxLimit:
            return self.maxLimit
        elif aVal < self.minLimit:
            return self.minLimit

        return aVal

    def __draw_power_history(self, i):
        '''
        Draw the audio signal level recorded history scene. Show the data as two
        lines, one for minimum level and one for maximum level over a
        background of sky light style gradients representing the time of day.

        Each entry is drawn at the skylight position representing when it was
        recorded.
        '''

        # How many signal level sets do we have
        if self.nMinHistory <= self.nMaxHistory:
            iCount = self.nMinHistory
        else:
            iCount = self.nMaxHistory
        iLast = iCount - 1

        # Get a scene to draw on
        view = self.findChild(QGraphicsView, "gvHistory")
        if view is not None:
            scene = self.__get_history_scene(view)

            # If the scene doesn't have the required height and width or we are
            # forcing a re-draw
            if (scene.height() != self.usefulHeight) or\
                    (scene.width() != self.usefulWidth) or\
                    (i != iLast):
                # debug_message("New scene rectangle")

                # Set a scene and draw the background
                self.__draw_history_background(view)

                # Get new scene
                scene = self.__get_history_scene(view)

                # No need to re-draw the background again for now
                self.forceNewBackground = False

                # Draw whole signal level data
                iPrv = 0
                i = 1
            else:
                # Just draw the most recent level data sets
                i = iCount - 1
                if i < 0:
                    i = 1
                iPrv = i - 1
                if iPrv < 0:
                    iPrv = 0

            xPrv = int(iPrv * self.xRatio)
            yMinPrv = None
            yMaxPrv = None
            while i < iCount:
                # Compute these only once and re-use them
                xPos = int(i * self.xRatio)

                # Only draw if the integer position on the scene changed
                if xPos > xPrv:
                    if i < self.nMinHistory:
                        # We need to scale and range limit the y values. The values
                        # are zero based so they need to have one subtracted from
                        # them
                        # Don't calculate  previous value every loop, it was
                        # previous loop's value unless it's the first loop
                        # iteration
                        if yMinPrv is None:
                            yMinPrv = 0.0 - self.minHistory[iPrv] * self.yRatio - 1.0
                            yMinPrv = self.__limit_data_point(yMinPrv,
                                                              self.usefulHeight)
                        yVal = 0.0 - self.minHistory[i] * self.yRatio - 1.0
                        yVal = self.__limit_data_point(yVal, self.usefulHeight)

                        scene.addLine(xPrv, yMinPrv, xPos, yVal, self.minPen)
                        yMinPrv = yVal
                    if i < self.nMaxHistory:
                        # Draw the max
                        if yMaxPrv is None:
                            yMaxPrv = 0.0 - self.maxHistory[iPrv] * self.yRatio - 1.0
                            yMaxPrv = self.__limit_data_point(yMaxPrv,
                                                              self.usefulHeight)
                        yVal = 0.0 - self.maxHistory[i] * self.yRatio - 1.0
                        yVal = self.__limit_data_point(yVal, self.usefulHeight)

                        scene.addLine(xPrv, yMaxPrv, xPos, yVal, self.maxPen)
                        yMaxPrv = yVal

                    # Use the current X position as the next iteration's
                    # previous x-position
                    xPrv = xPos

                iPrv = i
                i += 1

    def __draw_spectrum_history(self, i):
        '''
        Re-draw the spectrum history. The scene has floating point positioning
        but the view has integer positioning, the horizontal data is more than
        one entry per horizontal pixel and overlapped drawing of them is untidy
        so only draw when we pass an integer position on the scene.
        This might output multiple entries from the spectrum history so it has
        to use the spectrum mutex.
        FIXME: The output is really insensitive, all the power is in very low
               frequencies and the output contains no detail unless forced with
               something like a signal generator. I have tried multiple methods
               of "normalizing" the spectrum to see more detail but none has
               worked yet.
        '''

        # qCDebug(self.logCategory, "Drawing spectrum history from {}".format(i))

        # Get a scene to draw on
        view = self.findChild(QGraphicsView, "gvSpecHistory")
        if view is not None:
            # Get a scene to draw on
            scene = self.__get_history_scene(view)

            # Get the length and last index of spectrum data set
            self.fMutex.lock()
            iFreq = self.nfHistory - 1
            # qCDebug(self.logCategory, "Last frequency is {}".format(iFreq))

            # If the scene doesn't have the required height and width or we are
            # forcing a re-draw
            if (scene.height() != self.specUsefulHeight) or\
                    (scene.width() != self.usefulWidth) or\
                    (i < iFreq):
                # qCDebug(self.logCategory, "Re-drawing spectrum background scene")
                # Draw the background for the spectrum (not power level)
                self.__draw_history_background(view, isLevel=False)

                # qCDebug(self.logCategory, "Background for i: {}".format(i < iFreq))

                # Get any new scene
                scene = self.__get_history_scene(view)

                # Don't need to re-draw background again for now
                self.forceNewBackground = False
            else:
                # FIXME: Are we overdrawing the same line?
                if i == self.iLastDrawn:
                    msg = "Over-drawing line spectrum at "
                    msg += "horizontal position {}".format(i)
                    qCWarning(self.logCategory, msg)

            while i <= iFreq:
                # Calculate the horizontal drawing position once
                xPos = i * self.xRatio
                # if i >= iFreq:
                #     msg = "Drawing spectrum at "
                # else:
                #     msg = "Re-drawing scrolled spectrum at "
                # msg += "X-position {} in __draw_spectrum_history".format(xPos)
                # qCDebug(self.logCategory, msg)

                # Get the spectrum data
                specData = self.fHistory[i]

                if i == iFreq:
                    pwrSum = specData.sum()
                    # min() doesn't match manually found minimum
                    # pwrMin = specData.min()
                    pwrMin = self.__my_min(specData)
                    pwrMax = specData.max()
                    rMin = -1.0
                    rMax = -1.0
                    rSum = -1.0
                else:
                    # Get the saved values instead
                    fScale = self.fScaling[i]
                    pwrMin = fScale[0]
                    pwrMax = fScale[1]
                    pwrSum = fScale[2]
                    rMin = self.__my_min(specData)
                    rMax = specData.max()
                    rSum = specData.sum()
                # msg = "Original spectrum data has sum {} ".format(pwrSum)
                # msg += "in range {} to {}".format(pwrMin, pwrMax)
                # qCDebug(self.logCategory, msg)

                # magnitude = numpy.abs(specData)
                # normalizedSpectData = (magnitude - numpy.min(magnitude)) / (numpy.max(magnitude) - numpy.min(magnitude))
                # normalizedSpectData = (magnitude - numpy.mean(magnitude)) / numpy.std(magnitude)

                # If we are dealing with the last FFT set it might be a sum and
                # need to be made a mean and set to our display alpha range
                # FIXME: This assumes we don't need to do this when scrolling
                #        the scene!
                # FIXME: I don't think we need this anymore, hence the + 1000
                #        placed in the conditional. We use rollingSpectrum while
                #        building data but the only data we show is that which
                #        appended on a timestep and that has already been
                #        converted to a ratio.
                # if i == (iFreq - 1):
                if i == (iFreq + 1000):
                    if pwrMax > 1.0:
                        # Convert all the values to ratios against max for this
                        # spectrum
                        # specData /= pwrMax
                        pwrMin /= pwrMax
                        pwrMax = 1.0

                        if self.spectrumIndB is True:
                            # For the dB style we now have ratios for dB
                            # converstion
                            dBMin = self.__dB(pwrMin)
                            dBScale = abs(dBMin)

                            # We have each frequency bin power as a ratio of max
                            iLast = len(specData) - 1
                            for iVal in range(0, iLast):
                                # Get the dB value, it has range from negative
                                # to zero
                                dBVal = self.__dB(specData[iVal])
                                # dBVal = self.__dB(normalizedSpectData[iVal])

                                # Re-range into positive
                                dBVal -= dBMin
                                if dBScale > 0.0:
                                    # Scale into the zero to 1.0 range
                                    dBVal /= dBScale
                                # And the chosen alpha range
                                # dBVal *= self.spectrumAlphaLimit
                                # Replace the ratio in the current spectrum
                                # frequency bin
                                specData[iVal] = dBVal

                            # We have new range values
                            pwrSum = specData.sum()
                            # min() doesn't match manually found minimum
                            # pwrMin = specData.min()
                            pwrMin = self.__my_min(specData)
                            pwrMax = specData.max()

                        # Convert to the alpha range
                        specData *= self.spectrumAlphaLimit
                        pwrMin *= self.spectrumAlphaLimit
                        pwrMax *= self.spectrumAlphaLimit
                        # if (pwrMin < 0.0) or (pwrMax > self.spectrumAlphaLimit):
                        msg = "Spectrum ratio data has "
                        msg += "range {} to {}".format(pwrMin, pwrMax)
                        qCDebug(self.logCategory, msg)
                # else:
                #     if rSum >= 0:
                #         msg = "Spectrum draw data has sum {} ".format(rSum)
                #         msg += "in range {} to {}".format(rMin, rMax)
                #         qCDebug(self.logCategory, msg)

                # Check if we have at least as many timestamps as spectrums
                if self.nfHistory != self.ntHistory:
                    msg = "TIME ({}) ".format(self.ntHistory)
                    msg += "AND SPECTRUM ({}) ".format(self.nfHistory)
                    msg += "ARRAYS ARE DIFFERENT LENGTHS"
                    qCDebug(self.logCategory, msg)

                # Draw the spectrum for this time-point
                # qCDebug(self.logCategory, "Drawing spectrum at {}".format(self.tHistory[i]))
                self.__draw_single_point_spectrum(i, iFreq, scene, xPos)

                self.iLastDrawn = i;
                i += 1

            # Finished with the spectrum history
            self.fMutex.unlock()

            # Draw a red blob to see vertical context (debug)
            # tmpPen = QPen(QColor("red"), 1, Qt.SolidLine,
            #               Qt.SquareCap, Qt.BevelJoin)
            # scene.addLine(10.0, 0.0, 20.0, 5.0, tmpPen)

            view.show()

    def __reverse_spectrum_mode(self):
        '''
        Take the whole spectrum data and reverse it from dB to power ratio or
        vice-versa based on the current mode
        '''

        iMaxSpectrum = self.nfHistory - 1
        for i in range(0, iMaxSpectrum):
            # Get the spectrum data at the current index
            specData = self.fHistory[i]

            # Last thing we did when creating it was convert to alpha range
            specData /= self.spectrumAlphaLimit

    def __reached_history_timestep(self):
        '''
        Use the time to work out if we have reached an expected time-step when
        we want to add new records to our day view logs.

        Returns: True if self.tPeriod has elapsed since the last time record,
                 else returns False

        We will log the new time-step here and the caller is responsible for
        logging all records associated with self.tPeriod before calling this
        function again.
        '''

        if self.tAudioStart > 0.0:
            self.timeStepChecks += 1
            if self.timeSteps > 0:
                # Once we start knowing the mean calls per-append use it to
                # avoid calling time.time repeatedly by exiting early based on
                # the count of calls since the last step to infer time to next.
                # To reduce errors we bisect the mean calls per-append and check
                # the time elapsed once on each bisection
                tsLastStep = self.timeStepChecks % self.timeStepMeanChecks
                if tsLastStep < self.timeStepNextCheck:
                    # Not likely we've reached the time-step, exit early
                    return False
                # Re-check half way between the current count and the mean calls
                # per-append
                self.timeStepNextCheck +=\
                        (self.timeStepMeanChecks - self.timeStepNextCheck) >> 1
                # qCDebug(self.logCategory, "timestep mean: {}, at {} next {}".format(self.timeStepMeanChecks, tsLastStep, self.timeStepNextCheck))


            # If we have any time history calculate the elapsed time since an
            # update
            tNow = time.time()
            if self.ntHistory > 0:
                elapsed = tNow - self.tHistory[self.ntHistory - 1]
            else:
                # Calculate the elapsed time since we started audio
                elapsed = tNow - self.tAudioStart

            # If we have elapsed the display update timeout
            if elapsed >= self.tPeriod:
                self.timeSteps += 1
                self.timeStepMeanChecks =\
                        int(self.timeStepChecks / self.timeSteps)
                self.timeStepNextCheck = self.timeStepMeanChecks >> 1
                # Reset base numbers every 25 appends a little over hourly in
                # current display
                # FIXME: Change this to use the view element time to create a
                #        a value that resets about hourly
                if self.timeSteps > 25:
                    self.timeStepChecks = self.timeStepMeanChecks
                    self.timeSteps = 1

                # self.tPeriod exceeded, log the new timestamp and return true
                self.tHistory.append(tNow)
                self.ntHistory += 1

                return True

        return False

    def __record_signal(self):
        '''
        Make a new record for min and max of signal level over the the current
        time period and reset the rolling values for the newly starting time
        period.
        '''

        # If we have no minRoll but do have a preMinRoll it's because the input
        # is extremely quiet and we were avoiding it thinking it was the effect
        # of starting sampling providing zero levels at the beginning therefore
        # not a real minimum. If we get here in that case we have to use the
        # preMin/Max rolling values
        if self.ntHistory == 1:
            if (self.minRoll == self.maxLimit)\
                    and (self.maxRoll == self.minLimit):
                self.minRoll = self.preMinRoll
                self.maxRoll = self.preMaxRoll

        # We draw signal levels min/max lines so make a record for each
        self.minHistory.append(self.minRoll)
        self.nMinHistory += 1
        self.maxHistory.append(self.maxRoll)
        self.nMaxHistory += 1

        # Reset the rolling min/max to excess values to get new min/max for
        # the new timestap being started
        self.minRoll = self.maxLimit
        self.maxRoll = self.minLimit

    def __convert_spectrum_dB_ratios_to_power(self, i=0):
        '''
        Assuming all the spectrum UI records are dB ratios, convert each to a
        power ratio. It can be used to convert fewer than the whole set of
        records if i is set. Use the spectrum mutex to prevent updates while we
        are modifying one or more entries in an array of arrays.
        '''

        self.fMutex.lock()

        # Walk from i to the end of the history
        while i < self.nfHistory:
            # Get the scene FFT for the bin to avoid double indexing in the
            # value loop. This has the overhead of requiring each FFT array
            # index being operated on having to be duplicated to work on then
            # the result duplicated again to replace the record in the history
            sceneFFT = self.fHistory[i]

            # Get the power scale for the index
            pwrRange = self.fScaling[i]
            pwrMin = pwrRange[0]
            pwrMax = pwrRange[1]
            pwrSum = pwrRange[1]

            # and the max possible for the audio thread.
            samplePeak = self.audioThread.sample_peak

            # For the power style we assume record i to the last record is in dB
            # ratio format
            pwrMinRatio = pwrMin / samplePeak
            dBMax = 0.0
            dBMin = self.__dB(pwrMinRatio)
            adBMin = abs(dBMin)

            # Scale it out of the alpha range
            sceneFFT /= self.spectrumAlphaLimit

            # We have each frequency bin as a ratio in dB over minimum dB for
            # all bins
            iLastFFT = len(sceneFFT)
            for iBinVal in range(0, iLastFFT):
                dBVal = sceneFFT[iBinVal]
                odBVal = dBVal

                # Scale back to the dB range
                dBVal *= adBMin

                # Re-range into negative through zero
                dBVal -= adBMin

                # Check for error values
                if dBVal > 0.0:
                    msg = "dB value exceeded at {}, ".format(iBinVal)
                    msg += "{} dB ratio ".format(odBVal)
                    msg += "becomes {} dB".format(dBVal)
                    qCDebug(self.logCategory, msg)

                # This is the original dB value, convert to power ratio
                pwrVal = self.__from_dB(dBVal)

                # Check for error values
                if (pwrVal < 0.0) or (pwrVal > 1.0):
                    msg = "Invalid value converting dB ratio {} ".format(odBVal)
                    msg += " gives power ratio {}".format(pwrVal)

                # Replace the ratio in the current spectrum
                # frequency bin
                sceneFFT[iBinVal] = pwrVal

            # Scale it to alpha range
            sceneFFT *= self.spectrumAlphaLimit

            # Replace the history entry with the scene value. It is the ratio
            # of bin dB and dB range for all bins
            self.fHistory[i] = sceneFFT

            i += 1

        self.fMutex.unlock()

    def __convert_spectrum_power_ratios_to_dB(self, i=0):
        '''
        Assuming all the spectrum UI records are simple power ratios, convert
        each to a dB (ratio of actual dB for each bin and dB range in the
        spectrum). It can be used to convert fewer than the whole set of records
        if i is set. Use the spectrum mutex to prevent updates while we are
        modifying one or more entries in an array of arrays.
        '''

        self.fMutex.lock()

        # Walk from i to the end of the history
        while i < self.nfHistory:
            # Get the scene FFT for the bin to avoid double indexing in the
            # value loop. This has the overhead of requiring each FFT array
            # index being operated on having to be duplicated to work on then
            # the result duplicated again to replace the record in the history
            sceneFFT = self.fHistory[i]

            # Each bin in the FFT is one half of the symmetric FFT and all bin
            # values have already been doubled to account for both bins

            # Get the power scale for the index, the values were all divided by
            # 2 when the reference power (full-scale * 2) was used to get the
            # power ratio
            pwrRange = self.fScaling[i]
            # pwrMin = pwrRange[0] * 2.0
            # pwrMax = pwrRange[1] * 2.0
            # pwrSum = pwrRange[1] * 2.0
            pwrMin = pwrRange[0]
            pwrMax = pwrRange[1]
            pwrSum = pwrRange[1]

            # msg = "Saved scale for index {}: ".format(i)
            # msg += "Min={}, Max={}, Sum={}".format(pwrMin, pwrMax, pwrSum)
            # qCDebug(self.logCategory, msg)

            # FIXME: This is probably unsafe, we forced the power ratios into
            #        the range 0...alphaLimit by clamping and then used the
            #        current data as a scale for the next power ratio and we
            #        don't have that scale here...

            liveMin = numpy.min(sceneFFT)
            # if liveMin == tmpMin:
            #     qCDebug(self.logCategory, "numpy.min(ndarray) works")
            liveMax = numpy.max(sceneFFT)
            liveSum = numpy.sum(sceneFFT)
            # msg = "Live FFT for index {}: ".format(i)
            # msg += "Min={}, Max={}, Sum={}".format(liveMin, liveMax, liveSum)
            # qCDebug(self.logCategory, msg)

            # and the max possible for the audio thread.
            samplePeak = self.audioThread.sample_peak # * 2.0
            # qCDebug(self.logCategory, "Sample peak is {}".format(samplePeak))

            # The indices are assumed to be power scales against samplePeak. So
            # the absolute value of the minimum signal as a dB is the shift we
            # need to apply to make the values all positive then the ratio of
            # that result and the absolute minimum dB value is the ratio to
            # display

            pwrMinRatio = pwrMin / samplePeak
            dBMax = 0.0
            dBMin = self.__dB(pwrMinRatio)
            adBMin = abs(dBMin)

            # We have each frequency bin power as a ratio of power max with a
            # constant alpha limit set. Remove the alpha limit.
            sceneFFT /= self.spectrumAlphaLimit

            iLastFFT = len(sceneFFT)
            for iBinVal in range(0, iLastFFT):
                # Calculate the dB value, it has range from negative to zero
                # dBVal = self.__dB(sceneFFT[iBinVal] * 2.0)
                dBVal = self.__dB(sceneFFT[iBinVal])
                odBVal = dBVal

                # Re-range into positive
                dBVal += adBMin
                # Scale into the zero to 1.0 range
                dBVal /= adBMin

                # Check for error values
                if (dBVal < 0.0) or (dBVal > 1.0):
                    msg = "dB ratio exceeded at {}, ".format(iBinVal)
                    msg += "{} dB ".format(odBVal)
                    msg += "from {} power ratio ".format(sceneFFT[iBinVal])
                    msg += "minimum {} ".format(dBMin)
                    msg += "gave ratio {}".format(dBVal)
                    qCDebug(self.logCategory, msg)

                    # Correct, but this is loss of detail
                    if dBVal < 0.0:
                        dBVal = 0.0
                    elif dBVal > 1.0:
                        dBVal = 1.0

                #  Replace the ratio in the current spectrum
                # frequency bin
                sceneFFT[iBinVal] = dBVal

            # Scale it into alpha range
            sceneFFT *= self.spectrumAlphaLimit

            # Replace the history entry with the scene value. It is the ratio
            # of bin dB and dB range for all bins
            self.fHistory[i] = sceneFFT

            i += 1

        self.fMutex.unlock()

    def __record_spectrum(self):
        '''
        Make a new record for spectrum data, including converting it to a ratio
        but making a record of the min, max and sum. Convert down from the FFT
        size to the UI size now (once for the whole rolled spectrum)
        FIXME: The problem with this is that to get any detail requires a long
               sample stream, but it can't be as long as a pixel represents in
               the day view (guaranteeing the data used and displayed is
               partial) and regardless, the number of samples for even a few
               seconds makes the FFT giant, making downscaling it to the height
               of the day view very expensive...The best hope of some detail and
               full time-domain is to sum smaller FFTs...as long as it doesn't
               average out the detail...
        '''

        # First get space to convert down from the source FFT size to one that
        # has the same number of elements as in the UI height
        sceneFFT = numpy.zeros((int(self.specUsefulHeight)))
        scenefStep = (1.0 * self.nyquistFrequency)\
                / (1.0 * self.specUsefulHeight)

        # fN = self.audioThread.nyquist_frequency
        # qCDebug(self.logCategory, "Nyquist frequency is {} or {}".format(self.nyquistFrequency, fN))

        # Get the FFT information and frequency list for the source
        srcfBins = self.audioThread.fft_data
        # pScale = self.audioThread.fft_normalizer_value
        # pScale = 1.0
        srcFreqBins = self.audioThread.fft_freqs

        # If we got it all
        if (sceneFFT is not None) and (srcfBins is not None) and\
                (srcfBins is not None):
            # Work out the frequency count for the source
            srcnBins = srcfBins.size
            srcnFreqs = srcFreqBins.size

            # If we got the expected Hermitian symmetric FFT data
            # binMax = numpy.max(srcfBins)
            # binMin = numpy.max(srcfBins)
            if (srcnFreqs - 1) == ((srcnBins - 1) / 2):
                # qCDebug(self.logCategory, "Symmetric FFT in {} with max {}, min{}".format(type(srcfBins), binMax, binMin))
                # Use frequency count as bin count, we have conjugate symmetry
                # in the FFT data and only need to use the indices from 1 to
                # the Nyquist frequency. Index 0 is the data sum so we don't
                # use it. Slice the FFT data from 1 and use the size of useful
                # FFT bins
                srcnBins = srcnFreqs - 1
                srcfBins = srcfBins[1:srcnBins]
                srcFreqBins = srcFreqBins[1:srcnBins]
                srcnBins = srcfBins.size
                srcfStep = (1.0 * self.nyquistFrequency) / (1.0 * srcnBins)
                # qCDebug(self.logCategory, "Sliced source has {} bins, {} frequencies, step is {} Hz, Nyquist {}Hz".format(srcnBins, srcnFreqs, srcfStep, self.nyquistFrequency))
            elif srcnFreqs != srcnBins:
                # qCDebug(self.logCategory, "Non-symmetric FFT ({}/{}) with max {}".format(srcnFreqs, srcnBins, binMax))
                srcfBins = srcfBins[1:srcnBins]
                srcFreqBins = srcFreqBins[1:srcnBins]
                srcnBins = srcfBins.size
                srcfStep = (1.0 * self.nyquistFrequency) / (1.0 * srcnBins)
                # Mis-matched FFT bin and frequency counts, we'll try using the
                # apparent source frequency bins
                # qCDebug(self.logCategory, "Source has {} bins, {} frequencies, step is {} Hz, Nyquist {}Hz".format(srcnBins, srcnFreqs, srcfStep, self.nyquistFrequency))

            # binMax = numpy.max(srcfBins)
            # qCDebug(self.logCategory, "Max after slice is {}".format(binMax))

            # Get the magnitude of the frequency bins and double the values to
            # compensate for symmetry without considering it.
            # srcfBins = numpy.abs(srcfBins)
            srcfBins *= 2.0

            # Make sure there are at least as many vertical pixels as
            # FFT bins
            if srcnBins < self.specUsefulHeight:
                msg = "Not enough frequency bins {} for ".format(srcnBins)
                msg += "spectral view height {}".format(self.specUsefulHeight)
                qCWarning(self.logCategory, msg)

            # qCDebug(self.logCategory, "Scaled source pwr density peak: {} of {} bins, scaling to {}".format(numpy.max(srcfBins), srcnBins, self.specUsefulHeight))

            # Re-combine source bins into the height range of the scene
            nextSrcStartBin = 0
            sceneHeight = int(self.specUsefulHeight)
            sceneLastPoint = sceneHeight - 1
            # maxScene = 0
            # qCDebug(self.logCategory, "Recombining {} source bins into {} scene bins with {} source frequencies".format(srcnBins, sceneHeight, srcFreqBins.size))
            for aSceneBin in range(0, sceneHeight):
                # The scene point and the scene frequency steps let us
                # calculate the start and end frequencies we are converting into
                # We have to be careful how we use them or we can ignore one
                # source bin.
                scenefStart = aSceneBin * scenefStep
                scenefEnd = scenefStart + scenefStep
                # qCDebug(self.logCategory, "Scene bin from {} to {}, step {}".format(scenefStart, scenefEnd, scenefStep))

                # Work from the last saved source bin
                aSrcBin = nextSrcStartBin
                srcBinFreq = srcFreqBins[aSrcBin]

                # Track the number of source bins combined while combining them
                # into a scene bin
                nCombined = 0
                # qCDebug(self.logCategory, "Scene bin {} combining from {} to {}".format(aSceneBin, srcBinFreq, scenefEnd))
                while srcBinFreq <= scenefEnd:
                    if aSrcBin < srcnBins:
                        # qCDebug(self.logCategory, "Source bin {} is in range {}".format(aSrcBin, srcnBins))
                        # Do something to scale the source bins to see more
                        # detail. It needs to be frequency relative, larger
                        # contribution at higher frequencie. Values in the data
                        # should be less than 1.0

                        srcVal = srcfBins[aSrcBin]
                        # if srcVal > maxScene:
                        #     maxScene = srcVal

                        if srcVal < 0.0:
                            srcVal = 0 - srcVal
                        # if srcVal > 1.0:
                        #     srcVal /= 2.0

                        # Current bin is for a source bin between start and end,
                        # use it as the index of the fft and sum values into the
                        # scene umtil we reach the end frequency for the current
                        # scene bin, while tracking the number we combine
                        # if srcVal > sceneFFT[aSceneBin]:
                        #     sceneFFT[aSceneBin] = srcVal
                        sceneFFT[aSceneBin] += srcVal
                        nCombined += 1

                    # Next source bin
                    aSrcBin += 1
                    # if aSrcBin < srcFreqBins.size:
                    if aSrcBin < srcnBins:
                        srcBinFreq = srcFreqBins[aSrcBin]
                    else:
                        # We just used the last source bin, cause the while loop
                        # to exit
                        srcBinFreq = scenefEnd + 1.0

                # Save where we ended for the next scene bin
                nextSrcStartBin = aSrcBin
                lastUsedSceneBin = aSceneBin

                # Scale each scene bin based on number of combined source bins
                # and the accumulated FFT sums in the audio thread
                # if nCombined > 0:
                #     sceneFFT[aSceneBin] /= (pScale * nCombined)
                # else:
                #     # qCDebug(self.logCategory, "NO combined data in {} bins".format(x))
                #     sceneFFT[aSceneBin] /= pScale
                if nCombined > 0:
                    sceneFFT[aSceneBin] /= nCombined

                # qCDebug(self.logCategory, "Combined pwr density peak: {} of {}".format(numpy.max(pwrMax), nCombined))

                # Report a bad scene value...
                # if (sceneFFT[aSceneBin] < 0.0) or (sceneFFT[aSceneBin] > 1.0):
                #     qCDebug(self.logCategory, "UNEXPECTED LEVEL RATIO: {}/{}".format(sceneFFT[aSceneBin], aSceneBin))
                #     qCDebug(self.logCategory, "                 SCALE: {}".format(pScale))

                #     # Use a spot high value, it probably should be a 1.0
                #     # constant
                #     # FIXME: This prevents detecting a reason to change one of
                #     #        the scales applied above
                #     # sceneFFT[aSceneBin] = 1.0

            # Did we fill as many scene bins as there are vertical pixels?
            if lastUsedSceneBin != sceneLastPoint:
                msg = "SCALE DOWN FFT TO SCENE "
                msg += "{} ".format(int(self.specUsefulHeight))
                msg += "DIDN'T FILL {} SCENE".format(lastUsedSceneBin + 1)
                qCWarning(self.logCategory, msg)

            # qCDebug(self.logCategory, "Scaled scene pwr density peak: {} of {} bins".format(numpy.max(sceneFFT), self.specUsefulHeight))

            # FIXME: Which one do we need, the before ratio scaling here or the
            #        after ratio scaling later
            # Get the scale details
            # pwrMin = numpy.min(sceneFFT)
            pwrMax = numpy.max(sceneFFT)
            # pwrSum = sceneFFT.sum()
            # self.powerScaling = ( pwrMin, pwrMax, pwrSum )
            # qCDebug(self.logCategory, "Max after scene is {}, seen during was {}".format(pwrMax, maxScene))


            # Scale again into 0...1 for scene
            if pwrMax > 0:
                sceneFFT /= pwrMax

            # Set maximum to the alpha limit
            sceneFFT *= self.spectrumAlphaLimit

            # If we get here then sceneFFT has the UI version of the original
            # FFT data as a signal level power ratio. Gather data and make a
            # record based on enabled format
            # FIXME: These never get used because we forced the bin value to
            #        the alpha level when it was too high above
            pwrMin = numpy.min(sceneFFT)
            pwrMax = numpy.max(sceneFFT)
            pwrSum = sceneFFT.sum()
            self.powerScaling = ( pwrMin, pwrMax, pwrSum )
            if (pwrMin < 0.0) or (pwrMax > self.spectrumAlphaLimit):
                msg = "UNEXPECTED spectrum ratios, minimum: {}, ".format(pwrMin)
                msg += "maximum: {}, ".format(pwrMax)
                msg += "sum: {}, ".format(pwrSum)
                qCDebug(self.logCategory, msg)

                # Force any excessive values into range
                for aSceneBin in range(0, sceneHeight):
                    if sceneFFT[aSceneBin] < 0.0:
                        sceneFFT[aSceneBin] = 0.0
                    elif sceneFFT[aSceneBin] > self.spectrumAlphaLimit:
                        sceneFFT[aSceneBin] = self.spectrumAlphaLimit

            if (pwrMax < self.fftMinDetail):
                msg = "LOW DETAIL spectrum at {}, ".format(self.ntHistory)
                msg += "minimum: {}, ".format(pwrMin)
                msg += "maximum: {}, ".format(pwrMax)
                msg += "sum: {}, ".format(pwrSum)
                qCDebug(self.logCategory, msg)

            # Add the spectrum as-is to the history (it's not formatted but do
            # that in the record in the history
            self.fMutex.lock()
            self.fHistory.append(sceneFFT)
            self.nfHistory += 1
            self.fScaling.append(self.powerScaling)
            self.nfScaling += 1
            # self.audioThread.reset_FFT_data()

            if self.spectrumIndB:
                # If we need to convert the appended record to dB then do that
                iSpectrum = self.nfHistory - 1
                self.__convert_spectrum_power_ratios_to_dB(iSpectrum)

            self.fMutex.unlock()
        else:
            qCDebug(self.logCategory, "Failed to create UI sized FFT data")

    def __clean_redundant_history(self):
        '''
        When we reach the point where the history views are filled we need to
        reset their start position, remove elements scrolled out of view and
        re-draw them. This function removes the elements scrolled out of view
        in the scenes.
        '''

        if self.debugDayUpdates is False:
            # Work out the new start time from the first time item
            newStart = self.tHistory[0] + self.filledDayMetersSlide
        else:
            # But handle the debug update rate as a special case, we won't reach
            # the filledDayMetersSlide duration as a real time, so invent it's
            # size in the data we have
            x = self.ntHistory
            iStart = self.filledDayMetersSlide * x / self.kDaySeconds
            newStart = self.tHistory[int(iStart)]

        # Work out approximately how many columns that is and the target column
        # count as a result
        columnDuration = 86400.0 / self.usefulWidth
        slideColumns = int(self.filledDayMetersSlide / columnDuration)
        targetColumns = int(self.usefulWidth - slideColumns)
        if targetColumns < 0:
            targetColumns = 0

        # Remove all older elements
        ntOrigHist = self.ntHistory
        '''
        # FIXME: If the del happens a lot then slice will probably be faster
        while self.ntHistory > targetColumns:
                # Delete one item at a time and use the new length each time as
                # a limit for the other view content arrays
                del self.tHistory[0]
                self.ntHistory -= 1

                # Stop if we run out of data
                if self.ntHistory == 0:
                    break
        '''
        self.tHistory = self.tHistory[slideColumns:]
        self.ntHistory -= slideColumns
        # TEMP: Check if we misssed a zero base difference
        ntLen = len(self.tHistory)
        if self.ntHistory != ntLen:
            qCDebug(self.logCategory, "Error slicing on EOD slide: {}/{}".format(ntLen, self.ntHistory))

        # If we removed anything we re-draw the whole day views on next draw
        if self.ntHistory != ntOrigHist:
            self.scrollSpectrum = True

        # Reduce the view plot histories data to the same length as the time
        # history. Do each one on it's own to maximize the chance of each having
        # the same length as the timme history. It doesn't guarantee we have the
        # items from the same time history points but the chance is high of us
        # having the last <n> items from each, where <n> is the number of time
        # history points we have.
        # FIXME: These would be better slided as well
        '''
        while self.nMinHistory > self.ntHistory:
            del self.minHistory[0]
            self.nMinHistory -= 1
        while self.nMaxHistory > self.ntHistory:
            del self.maxHistory[0]
            self.nMaxHistory -= 1
        self.fMutex.lock()
        while self.nfHistory > self.ntHistory:
            del self.fHistory[0]
            self.nfHistory -= 1
        while self.nfScaling > self.ntHistory:
            del self.fScaling[0]
            self.nfScaling -= 1
        '''
        nSlice = self.nMinHistory - self.ntHistory
        if nSlice > 0:
            self.minHistory = self.minHistory[nSlice:]
            self.nMinHistory -= nSlice
        nSlice = self.nMaxHistory - self.ntHistory
        if nSlice > 0:
            self.maxHistory = self.maxHistory[nSlice:]
            self.nMaxHistory -= nSlice

        self.fMutex.lock()

        nSlice = self.nfHistory - self.ntHistory
        if nSlice > 0:
            self.fHistory = self.fHistory[nSlice:]
            self.nfHistory -= nSlice
        nSlice = self.nfScaling - self.ntHistory
        if nSlice > 0:
            self.fScaling = self.fScaling[nSlice:]
            self.nfScaling -= nSlice

        self.fMutex.unlock()

        '''
        This only existed to check for things like off-by-one errors due to
        things like zero base values and non-zero based computations but the
        failure cases have never been seen.
        if self.debugDayUpdates:
            # All the arrays should be no larger than the time history array
            # (although they can be shorter when there is missing data)
            if self.nMinHistory > self.ntHistory:
                msg = "CLEAN MINIMUMS IS LONGER THAN TIMES"
                qCDebug(self.logCategory, msg)
            if self.nMaxHistory > self.ntHistory:
                msg = "CLEAN MAXIMUMS IS LONGER THAN TIMES"
                qCDebug(self.logCategory, msg)
            if self.nfHistory > self.ntHistory:
                msg = "CLEAN SPECTRUMS IS LONGER THAN TIMES"
                qCDebug(self.logCategory, msg)
            if self.nfScaling > self.ntHistory:
                msg = "CLEAN SPECTRUM SCALES IS LONGER THAN TIMES"
                qCDebug(self.logCategory, msg)
        '''

    def __new_record(self):
        '''
        Handle new current audio level records, we only have to record at each
        timestep (self.tPeriod)

        Parameters: dBSignal - floating point signal level in dB
        '''

        if self.__reached_history_timestep():
            # msg = "TIMESTEP: Times before     {}".format(self.ntHistory)
            # qCDebug(self.logCategory, msg))
            self.__record_signal()
            # msg = "TIMESTEP: Spectrums before {}".format(len(self.fHistory)
            # qCDebug(self.logCategory, msg)
            self.__record_spectrum()
            # msg = "TIMESTEP: Spectrums after  {}".format(len(self.fHistory)
            # qCDebug(self.logCategory, msg)

            # Before drawing, make sure the scene has space and make some if not
            nTimes = self.ntHistory
            # msg = "TIMESTEP: Times after      {}".format(iTimes)
            # qCDebug(self.logCategory, msg)
            if nTimes <= self.usefulWidth:
                # Just draw the last index
                i = nTimes - 1
            else:
                # Need to make space and re-draw the whole scene
                self.__clean_redundant_history()
                i = 0

            # Now we should be able to draw our data
            self.__draw_power_history(i)
            self.__draw_spectrum_history(i)

    def __update_signal(self):
        '''
        Update the active state for the signal meter, this includes the
        displayed meter level and the rolling min/max during a time period
        '''

        # Get the dbValue for the most recent data and keep a copy
        try:
            # Get the current level (it might be better handled via the FFT
            # because it would allow only one set of values to be parsed,
            # the FFT bins. As it stands we parse the signal level data for
            # sum and parse the FFT data anyway.
            dBVal = self.audioThread.current_dB
        except ValueError:
            # Failed, assume a low value
            dBVal = -89.0

        # Keep value within limits
        dBVal = self.apply_limit_range(dBVal)

        # Only update the meter if the integer value hasn't changed since it
        # increases the set of values that won't cause a display update
        # idBVal = self.apply_limit_range(int(dBVal))
        # FIXME: This might be better if we didn't keep our own track of the
        #        last value set and used the progress bar's valueChanged signal
        #        instead
        idBVal = int(dBVal)
        if (idBVal != self.lastdB):
            # Changed signal value, show it and save it as the current value
            # start = time.perf_counter()
            self.ui.dBMeter.setValue(idBVal)
            # self.sumMeterSetDurations += time.perf_counter() - start
            # self.nMeterSets += 1
        '''
        This all gets done in the slot for the the changed value signal for
        the dBMeter
            self.lastdB = idBVal

        # Ignore absolute zeros before we have any records. The first few
        # returns from current_dB in the audio thread will be as-if the samples
        # are all zero, even in the presence of background noise.
        if self.ntHistory < 1:
            if dBVal <= self.minLimit:
                # Keep a roll of it in case we are in a sound-proof room...
                if dBVal < self.preMinRoll:
                    self.preMinRoll = dBVal
                if dBVal > self.preMaxRoll:
                    self.preMaxRoll = dBVal
                return

        # The rolling max/min can be updated at any time and we make a new
        # record at time steps and reset them when recorded.
        amChanged = False
        if dBVal > self.maxRoll:
            self.maxRoll = dBVal
            amChanged = True
            # debug_message("Max Roll {}, dbVal {}".format(self.maxRoll, dBVal))
        if dBVal < self.minRoll:
            self.minRoll = dBVal
            amChanged = True
            # debug_message("Min Roll {}, dbVal {}".format(self.minRoll, dBVal))
        if amChanged:
            if self.minRoll > self.maxRoll:
                msg = "Rolling minimum {} ".format(self.minRoll)
                msg += "is larger than maximum {}".format(self.maxRoll)
                qCWarning(self.logCategory, msg)

        # Note any changed absolute values and fix any error
        self.__keep_signal_absolute_max(dBVal)
        self.__keep_signal_absolute_min(dBVal)
        if self.absMin > self.absMax:
            self.reset_absolutes()
        '''
        '''
        amChanged = False
        if dBVal > self.absMax:
            aMax = dBVal
            amChanged = True
        else:
            aMax = self.absMax
        if dBVal < self.absMin:
            aMin = dBVal
            amChanged = True
        else:
            aMin = self.absMin

        # Keep track of absolute min/max that we've seen
        if amChanged:
            self.keep_signal_absolutes(aMin, aMax)
        '''

    def changed_level(self, value):
        '''
        Slot for the valueChanged signal from the dB meter

        Parameters
        ----------
            value: The new value set on the meter
        '''

        self.lastdB = value

        # Ignore absolute zeros before we have any records. The first few
        # returns from current_dB in the audio thread will be as-if the samples
        # are all zero, even in the presence of background noise.
        if self.ntHistory < 1:
            if value <= self.minLimit:
                # Keep a roll of it in case we are in a sound-proof room...
                if value < self.preMinRoll:
                    self.preMinRoll = value
                if value > self.preMaxRoll:
                    self.preMaxRoll = value
                return

        # The rolling max/min can be updated at any time and we make a new
        # record at time steps and reset them when recorded.
        amChanged = False
        if value > self.maxRoll:
            self.maxRoll = value
            amChanged = True
            # debug_message("Max Roll {}, dbVal {}".format(self.maxRoll, dBVal))
        if value < self.minRoll:
            self.minRoll = value
            amChanged = True
            # debug_message("Min Roll {}, dbVal {}".format(self.minRoll, dBVal))
        if amChanged:
            if self.minRoll > self.maxRoll:
                msg = "Rolling minimum {} ".format(self.minRoll)
                msg += "is larger than maximum {}".format(self.maxRoll)
                qCWarning(self.logCategory, msg)

        # Note any changed absolute values and fix any error
        self.__keep_signal_absolute_max(value)
        self.__keep_signal_absolute_min(value)
        if self.absMin > self.absMax:
            # Unusable min is greater than max (shouldn't happen)
            self.reset_absolutes()

    def __update_spectrum(self):
        '''
        We don't need to update the spectrum as long as the number of samples is
        changing we'll compute a new one when used. We just need to restart it
        for a new set of sample data which we'll do elsewhere.
        '''

        # Keep the Nyquist frequency known
        # FIXME: We can do this at start and zero it at end of sampling...
        self.nyquistFrequency = self.audioThread.nyquist_frequency

    def __update_meter(self):
        '''
        Do all meter and internal updates that are necessary
        '''

        # Only update when listening
        if self.audioThread is not None:
            # Update signal and spectrum data
            self.__update_signal()
            self.__update_spectrum()

            # Check for a time-period expiring and record records if so
            self.__new_record()

            # tNow = time.time()
            # if self.tLast == 0.0:
            #     self.tLast = tNow
            # else:
            #     tElapsed = tNow - self.tLast
            #     # qCDebug(self.logCategory, "timing: {}".format(tElapsed))
            #     if tElapsed >= 1.0:
            #         qCDebug(self.logCategory, "setValue {}, {}, {}".format(self.sumMeterSetDurations, self.nMeterSets, self.sumMeterSetDurations / self.nMeterSets))
            #         self.tLast = tNow

    def __keep_signal_absolute_min(self, aMin):
        '''
        Check a proposed minimum against the current absolute minimum and
        replace it if the proposed value is lower

        Parameters
        ----------
            aMin: Floating point number (dB, self-relative)
                A newly recorded minimum sample level
        '''

        if aMin < self.absMin:
            if aMin >= self.minLimit:
                # Supplied minimum is a new low and greater than or equal to the
                # minimum limit. Note and display the new absolute minimum
                self.absMin = aMin
                self.ui.lblAbsMin.setText("Min: {:.1f}".format(self.absMin))
            elif aMin:
                # Supplied minimum is less than minimum limit, start
                # re-considering downwards from the maximum limit
                self.absMin = self.maxLimit


    def __keep_signal_absolute_max(self, aMax):
        '''
        Check a proposed minimum against the current absolute minimum and
        replace it if the proposed value is lower

        Parameters
        ----------
            aMax: Floating point number (dB, self-relative)
                A newly recorded maximum sample level
        '''

        if aMax > self.absMax:
            if aMax <= self.maxLimit:
                # Supplied maximum is a new high and less than or equal to the
                # maximum limit. Note and display the new absolute maximum
                self.absMax = aMax
                self.ui.lblAbsMax.setText("Max: {:.1f}".format(self.absMax))
            else:
                # Supplied maximum is greater than maximum limit, start
                # re-considering upwards from the minimum limit
                self.absMax = self.minLimit

    def keep_signal_absolutes(self, aMin, aMax):
        '''
        Given what is expected to be a newly recorded minimum and maximum sound
        level, compare them with the absolute limit value members of the class
        instance, replace any of those that are exceeded and display any new
        absolute limits in the main window dialog.

        Note, if the new value exceeds the level control limits then reset the
        absolute value to the value that shows no new limit. This causes a new
        progression towards the limit. The reson for this is that when some
        devices are disabled then re-enabled (e.g. USB plug cycle) the minimum
        audio level becomes no signal while the device is disabled. This is
        below the level control minimum and if it was used as the absolute
        minimum it would used but never be exceeded even though it represents no
        sample data. The minimum or maximum in a given environment will hover
        around a relatively constant value so while this loses longer history it
        is unlikely to lose the picture of the observed limits.

        Parameters
        ----------
            aMin: Floating point number (dB, self-relative)
                A newly recorded minimum sample level
            aMax: Floating point number (dB, self-relative)
                A newly recorded maximum sample level
        '''
        if aMin < self.absMin:
            if aMin >= self.minLimit:
                # Supplied minimum is a new low and greater than or equal to the
                # minimum limit. Note and display the new absolute minimum
                self.absMin = aMin
                self.ui.lblAbsMin.setText("Min: {:.1f}".format(self.absMin))
            else:
                # Supplied minimum is less than minimum limit, start
                # re-considering downwards from the maximum limit
                self.absMin = self.maxLimit
        if aMax > self.absMax:
            if aMax <= self.maxLimit:
                # Supplied maximum is a new high and less than or equal to the
                # maximum limit. Note and display the new absolute maximum
                self.absMax = aMax
                self.ui.lblAbsMax.setText("Max: {:.1f}".format(self.absMax))
            else:
                # Supplied maximum is greater than maximum limit, start
                # re-considering upwards from the minimum limit
                self.absMax = self.minLimit

    def reset_absolutes(self):
        '''
        Reset the class instance absolute minimum and absolute maximum sample
        values to their state of least recorded information (minimum set to
        maximum limit; maximum set to minimum limit) and a new record of
        absolute limits starts. This is a slot for a UI button signal and allows
        things like resetting the limits to see limits at different times of
        day, e.g. night is quieter than day so what is the minimum/maximum in
        night/day as independent observation chosen by the user.
        '''
        self.absMin = self.maxLimit
        self.absMax = self.minLimit

    def __dB(self, value, peak=None):
        '''
        Calculate a dB value from either a value that's already a power ratio
        or a power value and a peak power
        '''

        # All zero values are minimum dB
        if value == 0.0:
            dBVal = self.fdBMin
        elif peak is None:
            # We can assume value is already a ratio
            dBVal = 20.0 * math.log10(value)
        else:
            # We have a value and peak, calculate the ratio and dB from it
            dBVal = 20.0 * math.log10(value / peak)

        return dBVal

    def __from_dB(self, dBVal):
        '''
        Given a dB value returns the ratio used to create it
        '''

        return 10.0 ** (dBVal / 20.0)

    def __my_min(self, a):
        '''
        For some reason numpy.ndarray.min() always returns zero, write my own
        min() for one axis
        '''

        axes = a.shape
        if len(axes) > 0:
            aMin = 9.0e90
            for pos in range(0, axes[0]):
                aVal = a[pos]
                if aVal < aMin:
                    aMin = aVal
        else:
            aMin = 0.0

        return aMin

    def __rescale_spectrum_history(self, todB=True):
        '''
        Take the spectrum history and re-scale it to dB based values if toDB is
        True or to power ratios if it is False
        FIXME: This doesn't work properly
        '''

        # Go through all spectrum history
        if self.nfHistory > 0:
            lScales = self.nfScaling
            for sIdx in range(0, fLen):
                if sIdx < lScales:
                    tScales = self.fScaling[sIdx]
                else:
                    # Unscaled frequency data (the one currently being set)
                    tScales = ( 1.0, 1.0, 1.0 )

                msg = "Re-scaling to dB is {}. ".format(todB)
                msg += "Min {}, Max {}, ".format(tScales[0], tScales[1])
                msg += "Sum {}".format(tScales[2])
                qCDebug(self.logCategory, msg)

                # All values are scaled to spectrumAlphaLimit for either
                # approach
                self.fHistory[sIdx] /= self.spectrumAlphaLimit

                # Get the range information
                pwrSum = self.fHistory[sIdx].sum()
                # pwrMin = self.fHistory[ltHist - 2].min()
                pwrMin = self.__my_min(self.fHistory[sIdx])
                pwrMax = self.fHistory[sIdx].max()

                msg = "Source data Min {}, Max {}, ".format(pwrMin, pwrMax)
                msg += "Sum {}".format(pwrSum)
                qCDebug(self.logCategory, msg)

                if todB:
                    # If we are going to dB then we currently have power ratios
                    pwrMin /= pwrMax
                    pwrMax = 1.0
                    dBMin = self.__dB(pwrMin)
                    dBScale = abs(dBMin)
                else:
                    # To convert to the power ratio style we have dB ratios
                    # so we will need the informaation used to scale them
                    dBMax = self.__dB(tScales[0] / tScales[2])
                    dBMin = self.__dB(tScales[1] / tScales[2])
                    dBScale = abs(dBMin)

                # Go through the frequency bins
                iLastBin = len(self.fHistory[sIdx])
                for iVal in range(0, iLastBin):
                    # To dB and from dB are reverse of each other
                    if todB:
                        # Get the power ratio in dB
                        dBVal = self.__dB(self.fHistory[sIdx][iVal])
                        # Re-range into positive
                        dBVal -= dBMin
                        if dBScale > 0.0:
                            # Scale into the 1.0 range
                            newVal = dBVal / dBScale
                        else:
                            newVal = dBVal
                    else:
                        # Get the dB ratio currently stored
                        rVal = self.fHistory[sIdx][iVal]
                        if dBScale > 1.0:
                            # Scale into the dB Range
                            rVal *= dBScale
                        # Re-range into a negative dB value
                        rVal += dBMin
                        # Get the power ratio from the dB value
                        newVal = self.__from_dB(rVal)

                    # Replace the ratio in the current spectrum frequency
                    # bin
                    self.fHistory[sIdx][iVal] = newVal

                # Get the new range information before alpha scaling
                pwrSum = self.fHistory[sIdx].sum()
                # pwrMin = self.fHistory[ltHist - 2].min()
                pwrMin = self.__my_min(self.fHistory[sIdx])
                pwrMax = self.fHistory[sIdx].max()

                msg = "Scaled destination data Min {}, Max {}, ".format(pwrMin, pwrMax)
                msg += "Sum {}".format(pwrSum)
                qCDebug(self.logCategory, msg)

                # Re-scale all bins to alpha range
                self.fHistory[sIdx] *= self.spectrumAlphaLimit

                # Get the new range information
                pwrSum = self.fHistory[sIdx].sum()
                # pwrMin = self.fHistory[ltHist - 2].min()
                pwrMin = self.__my_min(self.fHistory[sIdx])
                pwrMax = self.fHistory[sIdx].max()

                msg = "Alpha scaled destination data Min {}, Max {}, ".format(pwrMin, pwrMax)
                msg += "Sum {}".format(pwrSum)
                qCDebug(self.logCategory, msg)

    def __draw_single_point_spectrum(self, i, iFreq, scene, xPos):
        '''
        Given a scene and the index of a spectrum data set draw it at the x
        position on the scene.
        Should be called while holding self.fMutex.
        '''
        specData = self.fHistory[i]
        yColor = self.spectrumColor

        # Go through the vertical pixels in the scene. Zero is the top,
        # height() is the bottom, draw the spectrum the same way, 0Hz
        # at top, nyquist frequency at bottom
        lastMean = -1.0
        maxY = int(self.specUsefulHeight)
        for vPoint in range(0, maxY):
            # Ending vertical point for the line showing this pixel
            vNext = vPoint + 1.0

            # Get the FFT bin value, it's already a normalized power
            # or dB ratio in alpha range
            binRatio = specData[vPoint]
            if binRatio > 1.0:
                # Case that wasn't normalized
                msg = "FFT bogus at {}, ".format(vPoint)
                msg += "{} ({}/{}) ".format(xPos, i, iFreq)
                msg += "of {}".format(scene.height())
                msg += ", sum {}".format(specData[vPoint])
                msg += ", mean {}".format(binRatio)
                # qCWarning(self.logCategory, msg)
                meanVal = self.spectrumAlphaLimit

            # Use the FFT value as the alpha for the line we will draw
            # and create a pen from it
            if binRatio != lastMean:
                yColor.setAlphaF(binRatio)
                fftPen = QPen(yColor, 1, Qt.SolidLine, Qt.SquareCap,
                              Qt.BevelJoin)

                lastMean = binRatio

            # Draw the line (xratio is the same as for the signal level
            # view).
            # if (vPoint % 30) == 0:
            # if (vPoint == 0) or (vPoint == (maxY - 1)):
            #     msg = "FFT adding line at {}, {} ".format(xPos, vPoint)
            #     msg += "({}/{}) of {} ".format(i, iFreq, scene.height())
            #     msg += ", mean {}".format(meanVal)
            #     qCDebug(self.logCategory, msg)
            scene.addLine(xPos, 1.0 * vPoint,
                          xPos, vNext, fftPen)

    # FIXME: This might be inefficient, creates a QSettings for every use, e.g.
    # when used for loading latitude and longitude it creates and destroys two
    # QSettings objects. But, the calling code just looks tidier
    def __config_load_text(self, keyText, default=None, keyGroup=None,\
                         setting=None):
        '''
        Take a settings key name, a default value and, optionally, a key group
        name and existing QSettings object then load a persistent application
        settings from them.

        If the key group and setting object are both None (the default) the
        value will be loaded from the top (application) group layer.

        The key group name and a pre-existing QSettings for any group level at
        or below the top can be both supplied and the value for the key is
        loaded from the key at the level of the key group name under the level
        of the supplied setting object.

        parameters
        ----------
            keyText: string
                The name of the settings key to set the value of
            default: string
                A default value to use if the key doesn't exist
            keyGroup: string
                Key group to save the key and value under. Or None to save at
                the top level
            setting: QSettings object
                Parent QSettings object, e.g. at a group layer, to save the
                key and value under. Or None to save at the top level

        Returns
        -------
            The value of the specified key converted to a floating point value

        Exceptions
        ----------
            FIXME: NO! ValueError if the text value of the key is not the text of a number
        '''

        if setting is None:
            mySet = QSettings()
        else:
            mySet = setting

        if keyGroup is not None:
            mySet.beginGroup(keyGroup)
        # if keyGroup is not None:
        #     keyText = keyGroup + "/" + keyText

        try:
            if mySet.contains(keyText):
                theVal = mySet.value(keyText, default)
            else:
                raise EOFError
        except EOFError:
            theVal = default

        return theVal

    def load_persistent_bool(self, keyText, default="False", keyGroup=None,\
                             setting=None):
        '''
        Take a settings key name, a default value and, optionally, a key group
        name and existing QSettings object then load a persistent application
        setting from them. If a default is supplied it will be returned if the
        key does not exist.

        If the key group and setting object are both None (the default) the
        value will be loaded from the top (application) group layer.

        The key group name and a pre-existing QSettings for any group level at
        or below the top can be both supplied and the value for the key is
        loaded from the key at the level of the key group name under the level
        of the supplied setting object.

        parameters
        ----------
            keyText: string
                The name of the settings key to set the value of
            default: string
                A default value to use if the key doesn't exist. Provide as the
                text representation of a boolean, True or False (case as shown)
            keyGroup: string
                Key group to save the key and value under. Or None to save at
                the top level
            setting: QSettings object
                Parent QSettings object, e.g. at a group layer, to save the
                key and value under. Or None to save at the top level

        Returns
        -------
            The value of the specified key converted to a boolean value. If the
            key does not exist, False is returned.

        Exceptions
        ----------
            ValueError if the text value of the key is not the text of a boolean
        '''

        txtSetting = self.__config_load_text(keyText, default, keyGroup,\
                                             setting)
        if txtSetting == "True":
            value = True
        elif txtSetting == "False":
            value = False
        else:
            raise ValueError

        return value

    def load_persistent_int(self, keyText, default, keyGroup=None,\
                            setting=None):
        '''
        Take a settings key name, a default value and, optionally, a key group
        name and existing QSettings object then load a persistent application
        settings from them. If a default is supplied it will be returned if the
        key does not exist.

        If the key group and setting object are both None (the default) the
        value will be loaded from the top (application) group layer.

        The key group name and a pre-existing QSettings for any group level at
        or below the top can be both supplied and the value for the key is
        loaded from the key at the level of the key group name under the level
        of the supplied setting object.

        parameters
        ----------
            keyText: string
                The name of the settings key to set the value of
            default: string
                A default value to use if the key doesn't exist. Provide as the
                text representation of an integer number, e.g. "1", not 1
            keyGroup: string
                Key group to save the key and value under. Or None to save at
                the top level
            setting: QSettings object
                Parent QSettings object, e.g. at a group layer, to save the
                key and value under. Or None to save at the top level

        Returns
        -------
            The value of the specified key converted to an integer value

        Exceptions
        ----------
            ValueError if the text value of the key is not the text of a number
        '''

        return int(self.__config_load_text(keyText, default, keyGroup, setting))

    def load_persistent_float(self, keyText, default, keyGroup=None,\
                              setting=None):
        '''
        Take a settings key name, a default value and, optionally, a key group
        name and existing QSettings object then load a persistent application
        settings from them. If a default is supplied it will be returned if the
        key does not exist.

        If the key group and setting object are both None (the default) the
        value will be loaded from the top (application) group layer.

        The key group name and a pre-existing QSettings for any group level at
        or below the top can be both supplied and the value for the key is
        loaded from the key at the level of the key group name under the level
        of the supplied setting object.

        parameters
        ----------
            keyText: string
                The name of the settings key to set the value of
            default: string
                A default value to use if the key doesn't exist. Provide as the
                text representation of a number, e.g. "0.5", not 0.5
            keyGroup: string
                Key group to save the key and value under. Or None to save at
                the top level
            setting: QSettings object
                Parent QSettings object, e.g. at a group layer, to save the
                key and value under. Or None to save at the top level

        Returns
        -------
            The value of the specified key converted to a floating point value

        Exceptions
        ----------
            ValueError if the text value of the key is not the text of a number
        '''

        return float(self.__config_load_text(keyText, default, keyGroup, setting))

    # FIXME: This might be inefficient, creates a QSettings for every use, e.g.
    # when used for saving latitude and longitude it creates and destroys two
    # QSettings objects. But, the calling just code looks tidier
    def save_persistent_text(self, keyText, newValue, keyGroup=None,\
                           setting=None):
        '''
        Take a settings key name, a text value for the key and, optionally, a
        key group name and existing QSettings object then create a persistent
        application settings from them.

        If the key group and setting object are both None (the default) the
        value will be saved at the top (application) group layer.

        The key group name and a pre-existing QSettings for any group level at
        or below the top can be both supplied and the value for the key is saved
        at the level of the key group name under the level of the supplied
        setting object.

        parameters
        ----------
            keyText: string
                The name of the settings key to set the value of
            newValue: float
                The value to set for the key
            keyGroup: string
                Key group to save the key and value under. Or None to save at
                the top level
            setting: QSettings object
                Parent QSettings object, e.g. at a group layer, to save the
                key and value under. Or None to save at the top level
        '''

        if setting is None:
            mySet = QSettings()
        else:
            mySet = setting

        if keyGroup is not None:
            mySet.beginGroup(keyGroup)

        mySet.setValue(keyText, newValue)
        if keyGroup is not None:
            mySet.endGroup()

    def save_persistent_bool(self, keyText, newValue, keyGroup=None, setting=None):
        '''
        Take a settings key name, a boolean value for the key and, optionally,
        a key group name and existing QSettings object then create a persistent
        application setting from them, the boot is saved as a test value.

        If the key group and setting object are both None (the default) the
        value will be saved at the top (application) group layer.

        The key group name and a pre-existing QSettings for any group level at
        or below the top can be both supplied and the value for the key is saved
        at the level of the key group name under the level of the supplied
        setting object.

        parameters
        ----------
            keyText: string
                The name of the settings key to set the value of
            newValue: boolean
                The value to set for the key
            keyGroup: string
                Key group to save the key and value under. Or None to save at
                the top level
            setting: QSettings object
                Parent QSettings object, e.g. at a group layer, to save the
                key and value under. Or None to save at the top level
        '''

        if newValue is True:
            valueText = "True"
        elif newValue is False:
            valueText = "False"
        else:
            raise ValueError

        self.save_persistent_text(keyText, valueText, keyGroup, setting)

    def save_persistent_int(self, keyText, newValue, keyGroup=None,\
                            setting=None):
        '''
        Take a settings key name, a new value and, optionally, a key group
        name and existing QSettings object then save a persistent application
        settings from them.

        If the key group and setting object are both None (the default) the
        value will be loaded from the top (application) group layer.

        The key group name and a pre-existing QSettings for any group level at
        or below the top can be both supplied and the value for the key is
        loaded from the key at the level of the key group name under the level
        of the supplied setting object.

        If the key group and setting object are both None (the default) the
        value will be saved at the top (application) group layer.

        The key group name and a pre-existing QSettings for any group level at
        or below the top can be both supplied and the value for the key is saved
        at the level of the key group name under the level of the supplied
        setting object.

        parameters
        ----------
            keyText: string
                The name of the settings key to set the value of
            newValue: integer
                The value to set for the key
            keyGroup: string
                Key group to save the key and value under. Or None to save at
                the top level
            setting: QSettings object
                Parent QSettings object, e.g. at a group layer, to save the
                key and value under. Or None to save at the top level
        '''

        # int will be translated automatically to text, keep the function
        # names tidy
        self.save_persistent_text(keyText, newValue, keyGroup, setting)

    def save_persistent_float(self, keyText, newValue, keyGroup=None, setting=None):
        '''
        Take a settings key name, a floating point value for the key and,
        optionally, a key group name and existing QSettings object then create
        a persistent application setting from them. The float is saved as a
        text value.

        If the key group and setting object are both None (the default) the
        value will be saved at the top (application) group layer.

        The key group name and a pre-existing QSettings for any group level at
        or below the top can be both supplied and the value for the key is saved
        at the level of the key group name under the level of the supplied
        setting object.

        parameters
        ----------
            keyText: string
                The name of the settings key to set the value of
            newValue: float
                The value to set for the key
            keyGroup: string
                Key group to save the key and value under. Or None to save at
                the top level
            setting: QSettings object
                Parent QSettings object, e.g. at a group layer, to save the
                key and value under. Or None to save at the top level
        '''

        # float will be translated automatically to text, keep the function
        # names tidy
        self.save_persistent_text(keyText, newValue, keyGroup, setting)

    def load_persistent_lat_lon(self):
        '''
        Load any persistent state for the latitude and longitude the application
        operates at into class state.

        If either does not exist then the assumed location is zero longitude on
        the equator.
        '''

        lat = self.load_persistent_float(self.kLatitude, "181.0")
        lon = self.load_persistent_float(self.kLongitude, "181.0")
        if (lat >= -90.0) and (lat <= 90.0) and (lon >= -180.0) and\
                (lon <= 180.0):
            # Set them locally
            self.latitude = lat
            self.longitude = lon
        else:
            # Invalid persistent value, assume zero longitude on the equator
            self.latitude = 0.0
            self.longitude = 0.0

        # Use them for time-of-day mathematics
        self.todCalc.set_latitude(self.latitude)
        self.todCalc.set_longitude(self.longitude)

        # centHour = int((lon / 15.0))
        # minHour = centHour - 1
        # maxHour = centHour + 1

        # Timezone clock offset
        # FIXME: 2022/12/20 This appears to never be used. A version is
        # available in seconds in self.todCalc but uses system time even if the
        # application is configured with a non-local latitude/longitude
        # self.tzOffset = 3600.0 * centHour
        # self.tzOffset = 1.0 * -3600.0
        self.tzOffset = 0.0

    def load_persistent_colors(self):
        '''
        Load persistent state for colors used in graphs, signal minimum,
        signal maximum and the spectrum. Color values are stored as the text
        format provided by QColor.name(), e.g. hex RGB string, #RRGGBB
        '''

        minColorText = self.__config_load_text(self.kMinColor)
        if minColorText is None:
            # Default
            minColorText = "green"
        self.minColor = QColor.fromString(minColorText)
        self.minPen = QPen(self.minColor,
                           1,
                           Qt.SolidLine,
                           Qt.SquareCap,
                           Qt.BevelJoin)

        maxColorText = self.__config_load_text(self.kMaxColor)
        if maxColorText is None:
            # Default
            maxColorText = "red"
        self.maxColor = QColor.fromString(maxColorText)
        self.maxPen = QPen(self.maxColor,
                           1,
                           Qt.SolidLine,
                           Qt.SquareCap,
                           Qt.BevelJoin)

        # We can only have a color for the spectrum, no pen. The color's alpha
        # can be changed for every pixel so the pen needs to be created for
        # every pixel.
        specColorText = self.__config_load_text(self.kSpecColor)
        if specColorText is None:
            # Default
            specColorText = "yellow"
        self.spectrumColor = QColor.fromString(specColorText)

    def load_persistent_view_spectrum_style(self):
        '''
        Load persistent state for the style of the daily spectrum view
        '''

        try:
            self.spectrumIndB = self.load_persistent_bool(self.kSpectrumIndB)
        except ValueError:
            # Asume power view if the pesistent value is bad
            self.spectrumIndB = False

        # msg = "Load spectrum view in dB {}".format(self.spectrumIndB)
        # qCDebug(self.logCategory, msg)

        self.__show_spectrum_style()

    def load_persistent_audio_window(self):
        try:
            self.windowFn = self.__config_load_text(self.kWindowType, "")
        except:
            # No window function on error
            self.windowFn = ""

    def load_persistent_audio_filter(self):
        '''
        Load persistent state for the audio filter to be applied to the spectrum
        view
        '''

        try:
            self.audioFilterName = self.__config_load_text(self.kFilterType, "")
            self.audioFilterLowF = self.load_persistent_int(self.kFilterLowF,
                                                            "0")
            self.audioFilterHighF = self.load_persistent_int(self.kFilterHighF,
                                                             "1")
            self.audioFilterOrder = self.load_persistent_int(self.kFilterOrder, "3")
        except ValueError:
            # No filter range on error
            self.audioFilterName = ""
            self.audioFilterLowF = 0
            self.audioFilterHighF = 1
            self.audioFilterOrder = 3

    def split_config_version_text(self, version):
        '''
        Assume version is in the format a.b.c where a, b and c are numbers and
        the whole makes up the configuration version format. Return a, b and c.
        Bad a is assumed 1;
        Bad b is assumed 0;
        Bad c is assumed 0
        '''

        # Split the version parts from the saved state, assumes 1 for bad major
        # zero for bad mid and zero for bad minor
        verSplit = version.find('.')
        if verSplit == -1:
            try:
                a = int(version)
            except:
                a = 1
            b = 0
            c = 0
        else:
            if verSplit == 0:
                a = 1
            else:
                try:
                    a = int(version[:verSplit])
                except:
                    a = 1

            verSplit += 1
            version = version[verSplit:]
            verSplit = version.find('.')
            if verSplit == -1:
                try:
                    b = int(version)
                except:
                    b = 0
                c = 0
            else:
                if verSplit == 0:
                    b = 0
                else:
                    try:
                        b = int(version[:verSplit])
                    except:
                        b = 0

                verSplit += 1
                version = version[verSplit:]
                try:
                    c = int(version)
                except:
                    c = 0

        return a, b, c

    def load_persistent_settings(self):
        '''
        Load all class (application) persistent state. Currently only latitude
        and longitude.
        '''

        # FIXME: Load only the saved version, compare it with the class member
        # version, create a function to convert persistent settings to higher
        # version models only. If loaded version is less than class member
        # version then convert saved settings to the model in this class (this
        # version) and re-save them before loading any persistent settings.
        savedStateVersion = self.__config_load_text(self.kStateVersion,
                                                    self.currentStateVersion)

        # Currently only version of my state version is supported
        '''
        if savedStateVersion != self.currentStateVersion:
            # FIXME: Split the version into parts, check if it is less than or
            # equal to my version and if it is, load the old state version
            # style that is saved, convert it to the current state version and
            # re-save as the new version style. Nothing to do for now.

            # The state version key was added after the latitude and longitude,
            # so there's a pseudo-previous version that's the really this
            # version missing a version number. The savedStateVersion we'll get
            # is None if that's the case, so only warn if the version is not
            # recognized and not None.
            if savedStateVersion != None:
                msg = "Unsupported saved state "
                msg += "version: {}".format(savedStateVersion)
                qCWarning(self.logCategory, msg)
                # warning_message(msg)
        '''

        # Split the version parts from the saved state
        vPersistMaj, vPersistMid, vPersistMin = self.split_config_version_text(savedStateVersion)

        # Load the parts we can expect to exist
        if vPersistMaj <= self.currentStateMaj:
            self.load_persistent_lat_lon()
            self.load_persistent_colors()
            self.load_persistent_view_spectrum_style()
        if (vPersistMaj >= 1) and (vPersistMid >= 1):
            # We can have audio window and filter settings
            self.load_persistent_audio_window()
            self.load_persistent_audio_filter()

        if savedStateVersion != None:
            # Re-save the loaded settings to persist generated values and
            # update version
            self.save_persistent_settings()

    def save_persistent_lat_lon(self):
        '''
        Make the class latitude and longitude members persistent application
        settings.
        '''

        self.save_persistent_float(self.kLatitude, self.latitude)
        self.save_persistent_float(self.kLongitude, self.longitude)

    def save_persistent_colors(self):
        '''
        Save persistent state for colors used in graphs, signal minimum,
        signal maximum and the spectrum. Color values are stored as the text
        format provided by QColor.name(), e.g. hex RGB string, #RRGGBB
        '''

        cName = self.minColor.name()
        self.save_persistent_text(self.kMinColor, cName)
        cName = self.maxColor.name()
        self.save_persistent_text(self.kMaxColor, cName)
        cName = self.spectrumColor.name()
        self.save_persistent_text(self.kSpecColor, cName)

    def save_persistent_view_spectrum_style(self):
        '''
        Save persistent state for the style of the daily spectrum view
        '''

        # msg = "Persistent spectrum style in dB is {}".format(self.spectrumIndB)
        # qCDebug(self.logCategory, msg)
        self.save_persistent_bool(self.kSpectrumIndB, self.spectrumIndB)

    def save_persistent_audio_window_function(self):
        '''
        Save persistent state for audio window function
        '''
        self.save_persistent_text(self.kWindowType, self.windowFn)

    def save_persistent_audio_filter(self):
        '''
        Save persistent state for the audio filter to be applied to the spectrum
        view
        '''

        self.save_persistent_text(self.kFilterType, self.audioFilterName)
        self.save_persistent_int(self.kFilterLowF, self.audioFilterLowF)
        self.save_persistent_int(self.kFilterHighF, self.audioFilterHighF)
        self.save_persistent_int(self.kFilterOrder, self.audioFilterOrder)

    def save_persistent_settings(self):
        '''
        Save all class (application) persistent state. Currently only latitude
        and longitude, view data colors and whether the spectrum view is dB or
        power relative
        '''

        # Saved state schema version
        self.save_persistent_text(self.kStateVersion, self.currentStateVersion)

        # Save the lat/lon persistently
        self.save_persistent_lat_lon()

        # Save the colors persistently
        self.save_persistent_colors()

        # Save the spectrum view style persistently
        self.save_persistent_view_spectrum_style()

        # Save the audio settings for the spectrum view
        self.save_persistent_audio_window_function()
        self.save_persistent_audio_filter()

    def save_settings_lat_lon(self, dlgConfig):
        '''
        Set the class latitude and longitude members from the values in controls
        in a settings dialog instance.

        parameters
        ----------
            dlgConfig: dlgSettings
                Settings dialog box class instance
        '''

        lat = dlgConfig.get_latitude_float()
        lon = dlgConfig.get_longitude_float()

        # Save them if there was a change
        if (self.latitude != lat) or (self.longitude != lon):
            self.latitude = lat
            self.longitude = lon

            # Make them persistent
            self.save_persistent_settings()

            # Use them for time-of-day mathematics
            self.todCalc.set_latitude(self.latitude)
            self.todCalc.set_longitude(self.longitude)

    def save_settings_colors(self, dlgConfig):
        '''
        Decide whether to save colors from settings dialog
        '''
        # Get the name value for minimum, maximum and spectrum colors in the
        # settings dialog
        nMin = dlgConfig.minimum_color.name()
        nMax = dlgConfig.maximum_color.name()
        nSpec = dlgConfig.spectrum_color.name()
        # debug_message("Config min color {}".format(nMin))
        # debug_message("Config max color {}".format(nMax))
        # debug_message("Config spec color {}".format(nSpec))

        # Assume no colors are changing
        cChange = False

        # Check each settings dialog color's name against the name for the same
        # color use in this object and if they differ, replace the one in this
        # object with the one from the settings dialog and note the change
        # Repeats for minimum, maximum and spectrum colors
        if nMin != self.minColor.name():
            # debug_message("Before: {}".format(self.minColor.name()))
            self.minColor = QColor.fromString(nMin)
            # debug_message("After: {}".format(self.minColor.name()))
            cChange = True

        if nMax != self.maxColor.name():
            self.maxColor = QColor.fromString(nMax)
            cChange = True

        if nSpec != self.spectrumColor.name():
            self.spectrumColor = QColor.fromString(nSpec)
            cChange = True

        # If we made any changes make settings persistent
        if cChange is True:
            self.save_persistent_settings()

    def save_settings_audio_window(self, dlgConfig):
        '''
        Save any audio window that's enabled
        '''

        wfnOn = dlgConfig.audio_windowing_enabled
        if wfnOn:
            curWindowFn = dlgConfig.window_function_type
            if self.windowFn != curWindowFn:
                self.windowFn = curWindowFn
                if self.audioThread is not None:
                    self.audioThread.set_window_type(curWindowFn)
                self.save_persistent_settings()

    def save_settings_audio_filter(self, dlgConfig):
        '''
        Save any audio filter that's enabled
        '''

        afOn = dlgConfig.audio_filter_enabled
        if afOn is True:
            curFilter = dlgConfig.audio_filter_type
        else:
            curFilter = ""
        if curFilter != "":
            curFilterLowF = dlgConfig.audio_filter_low_frequency
            curFilterHighF = dlgConfig.audio_filter_high_frequency
            curFilterOrder = dlgConfig.audio_filter_order


        # Store new filter if anything changed
        cChange = False
        if self.audioFilterName != curFilter:
            self.audioFilterName = curFilter
            cChange = True
        if curFilter != "":
            if self.audioFilterLowF != curFilterLowF:
                self.audioFilterLowF = curFilterLowF
                cChange = True
            if self.audioFilterHighF != curFilterHighF:
                self.audioFilterHighF = curFilterHighF
                cChange = True
            if self.audioFilterOrder != curFilterOrder:
                self.audioFilterOrder = curFilterOrder
                cChange = True

        if cChange is True:
            if self.audioThread is not None:
                self.audioThread.set_filter_type(curFilter)
                if curFilter != "":
                    self.audioThread.set_filter_low_f(curFilterLowF)
                    self.audioThread.set_filter_high_f(curFilterHighF)
                    self.audioThread.set_filter_order(curFilterOrder)
            self.save_persistent_settings()

    def __show_spectrum_style(self):
        # Describe the new style in the view
        if self.spectrumIndB is True:
            self.ui.rbSpectrumRatiodB.setChecked(True)
        else:
            self.ui.rbSpectrumRatioPower.setChecked(True)

    def __change_fft_item_mode(self, i):
        '''
        Change the dB/power-ratio mode of a fft scene view item at index i to
        the current mode, assuming it's current content is in the other view.
        '''

        if i <= self.nfHistory:
            # Get the FFT
            fftBins = self.fHistory[i]

            # ...and the scale information, split it into the elements
            fftScale = self.fScaling[i]
            pwrMin = fftScale[0]
            pwrMax = fftScale[1]
            pwrSum = fftScale[2]

            # Remove the scaling to the alpha limit
            fftBins /= self.spectrumAlphaLimit

            # Walk the bins
            iLastBin = len(fftBins)
            for n in range(0, iLastBin):
                aVal = fftBins[n]

                # We assume the current value of spectrumIndB has just been
                # reversed
                if self.spectrumIndB is True:
                    # Reverse the case of the data being in power ratio

                    # We currently have the power ratio, walk each element
                    # iLastPwr = iLastBin - 1
                    iLastPwr = iLastBin
                    for m in range(0, iLastPwr):
                        # convert it to dB and use it
                        dBVal = self.__dB(fftBins[m])
                        fftBins[m] = dBVal

                    # Now we have all data in dB it will have the range from
                    # minimum negative dB value to zero and we want it in the
                    # range zero to 1.
                    dBMin = numpy.min(fftBins)
                    adBMin = abs(dBMin)
                    fftBins += adBMin
                    fftBins /= adBMin
                else:
                    # Reverse the case of the data being in dB

                    # Get the minimum power ratio in dB
                    dBMin = self.__dB(pwrMin / self.audioThread.sample_peak)
                    adBMin = abs(dBMin)

                    # Convert the FFT to dB
                    fftBins *= adBMin
                    fftBins -= adBMin

                    # We have the dB values, walk them to make each a power
                    # ratio
                    iLastdB = iLastBin
                    for m in range(0, iLastdB):
                        pwrRatio = self.__from_dB(fftBins[m])
                        fftBins[m] = pwrRatio

            # Re-apply the alpha limit
            fftBins *= self.spectrumAlphaLimit

            # Re-store in the array of all FFTs
            self.fHistory[i] = fftBins

    def __change_mode_of_all_ffts(self):
        '''
        Reverse the mode of all FFT data
        '''

        if self.spectrumIndB is True:
            self.__convert_spectrum_power_ratios_to_dB(0)
        else:
            self.__convert_spectrum_dB_ratios_to_power(0)

    def save_settings_view_spectrum(self, showIndB = False):
        '''
        Accept and save a spectrum view change then show the new view
        Parameters
        ----------
            showIndB: Boolean indicating view should be in dB if True, in power
                      ratio if False
        '''

        if self.spectrumIndB != showIndB:
            # View mode changed, save it
            self.spectrumIndB = showIndB
            self.save_persistent_settings()

            # Fix the FFT data mode for all current FFT
            self.__change_mode_of_all_ffts()

            # Re-draw the view in the new style
            self.__draw_spectrum_history(0)

    def __dB_spectrum_view_toggled(self, checked):
        if checked:
            # If it became checked, make it class state, save if needed
            self.save_settings_view_spectrum(True)

    def __power_spectrum_view_toggled(self, checked):
        if checked:
            # If it became checked, make it class state, save if needed
            self.save_settings_view_spectrum(False)

    def __current_latlon(self):
        '''
        Get a tuple of the latitude and longitude in numeric format.
        '''

        return (self.latitude, self.longitude)

    def __current_colors(self):
        '''
        Get the configurable colors as a tuple of all, each in text format.
        '''
        return (self.minColor.name(), self.maxColor.name(),
                self.spectrumColor.name())

    def save_settings(self, dlgConfig):
        '''
        Save all settings from a settings dialog into persistent and class
        state. We can use members of this class to decode the state of dlgConfig
        without changing it (without reproducing it)

        parameters
        ----------
            dlgConfig: dlgSettings
                Settings dialog box class instance
        '''

        # FIXME: These each save all other settings
        self.save_settings_lat_lon(dlgConfig)
        self.save_settings_colors(dlgConfig)
        self.save_settings_audio_window(dlgConfig)
        self.save_settings_audio_filter(dlgConfig)

    def settings(self):
        '''
        Slot to handle a click of the settings button. Creates an instance of
        the settings dialog class, initializes it's values and displays it. If
        the settings dialog ends via user accepting the settings then save any
        changes persistently and to self.

        Avoid using functions that take the dialog to populate values because
        that requires the modified dialog be returned and re-assigned to
        dlgConfig in this function. Instead, use functions to get related values
        as a tuple and have members in the dialog that take the same tuple to
        populate it's state and only work on a single instnce of the local
        dlgConfig.
        '''

        dlgConfig = dlgSettings()

        # Populate the latitude, longitude and colors
        latlon = self.__current_latlon()
        dlgConfig.set_latlon(latlon)
        colors = self.__current_colors()
        dlgConfig.set_colors(colors)

        if self.audioFilterName != "":
            dlgConfig.enable_audio_filter()
            filt = self.audioFilterName
            lowF = self.audioFilterLowF
            highF = self.audioFilterHighF
            order = self.audioFilterOrder
            dlgConfig.set_audio_filter_type(filt)
            dlgConfig.set_audio_filter_low_f(lowF)
            dlgConfig.set_audio_filter_high_f(highF)
            dlgConfig.set_audio_filter_order(order)
        else:
            dlgConfig.disable_audio_filter()

        # Manage the window function
        if self.windowFn != "":
            dlgConfig.enable_window_function()
            exists = dlgConfig.window_function_exists(self.windowFn)
            if exists is True:
                dlgConfig.set_window_function_type(self.windowFn)
            else:
                dlgConfig.disable_window_function()
        else:
            dlgConfig.disable_window_function()

        # Manage the checkbox that sets the view update rate
        if self.debugDayUpdates is True:
            dlgConfig.enable_fast_view_updates()
        else:
            dlgConfig.disable_fast_view_updates()

        result = dlgConfig.exec()
        if result == QDialog.Accepted:
            self.save_settings(dlgConfig)

            # Fast view updates isn't a persistent state
            self.debugDayUpdates = dlgConfig.use_fast_view_updates
            self.__set_update_period()

    def app_accepted(self):
        '''
        Application exited via OK, make sure any running audio thread is
        stopped before using the parent class OK exit slot.
        '''

        if self.audioThread is not None:
            self.toggle_meter(False)

        self.accept()

    def app_rejected(self):
        '''
        Application exited via Cancel, make sure any running audio thread is
        stopped before using the parent class Cancel exit slot.
        '''

        if self.audioThread is not None:
            self.toggle_meter(False)

        self.reject()

    def connect_controls(self):
        '''
        Connect Qt signals to slots
        '''

        self.ui.buttonBox.accepted.connect(self.app_accepted)
        self.ui.buttonBox.rejected.connect(self.app_rejected)
        self.ui.pbStartStop.clicked.connect(self.toggle_meter)

        self.ui.pbSettings.clicked.connect(self.settings)

        self.ui.dBMeter.valueChanged.connect(self.changed_level)

        self.ui.tbResetAbs.clicked.connect(self.reset_absolutes)

        self.ui.dsbSampleWindow.valueChanged.connect(self.changed_sample_window)
        self.ui.dsbUpdatePeriod.valueChanged.connect(self.changed_update_period)
        self.ui.sbFramesPerSecond.valueChanged.connect(self.change_update_Hz)
        self.ui.cbAutoWindow.stateChanged.connect(self.changed_auto_window)
        self.ui.cbSampleHz.currentIndexChanged.connect(self.changed_sample_Hz)
        self.ui.cbSampleSize.currentIndexChanged.connect(self.changed_sample_size)

        self.ui.rbSpectrumRatiodB.toggled.connect(self.__dB_spectrum_view_toggled)
        self.ui.rbSpectrumRatioPower.toggled.connect(self.__power_spectrum_view_toggled)

        self.updateTimer.timeout.connect(self.__update_meter)

'''
Program entry point.

Enable debug and warning console messages. Create the application, create a
list of locations for icons to add to the theme search paths. Create an instance
of the QtMeter dialog class and show it. Exit the application when the dialog
main window is no longer shown.
'''
if __name__ == "__main__":
    QLoggingCategory.setFilterRules("QtMeter.*.debug=true\n"
                                    "QtMeter.*.warning=true\n"
                                    "QtMeter.*.info=true")
    # qSetMessagePattern("%{category} %{message}")
    # qSetMessagePattern("%{file}(%{line}): %{message}")
    qSetMessagePattern("%{message}")

    sys.argv = []
    #sys.argv += ['-platform', 'Fusion:lightmode=2']

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Create a search path list for icons in the theme. The first is scalable
    # icons that include list-add and list-remove for the settings dialog. The
    # second has a scalable camera-photo icon for the application. The third
    # isn't used because evolution can't be guaranteed installed where this is
    # used but it includes nicer colored list-add and list-remove than the
    # HighContrast defaults
    iconSearchPaths = []
    iconSearchPaths.append("/usr/share/icons/hicolor/scalable/apps")
    iconSearchPaths.append("/usr/share/icons/Adwaita/scalable/devices")
    iconSearchPaths.append("/usr/share/icons/HighContrast/scalable/actions")
    iconSearchPaths.append("/usr/share/icons/HighContrast/scalable/devices")
    iconSearchPaths.append("/usr/share/icons/breeze/devices/symbolic")
    # iconSearchPaths.append("/usr/share/evolution/icons/hicolor/48x48/status")
    QIcon.setFallbackSearchPaths(iconSearchPaths)

    widget = QtMeter()
    widget.show()

    sys.exit(app.exec())
