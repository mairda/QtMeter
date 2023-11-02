# This Python file uses the following encoding: utf-8
#
# This file is part of QtMeter.
#
# QtMeter is an extremely basic example of an audio level meter as a Qt
# application in Python. The development used python3.10 and PySide 6.3. It also
# uses the following python libraries:
# pyaudio, numpy, math
#
# Note that no reference audio level is available unless you know the value to
# add in your own case so the apparent dB level displayed by the meter is NOT a
# SPL and is only a self-relative dB value. However, the point is that in a few
# hundred lines of python it demonstrates reading audio sample data and
# displaying a tunable level meter for the sample data.
#
# It uses a thread to receive audio samples and keeps a rolling moving average
# of the amplitude. The duration of the rolling average can be tuned using the
# "Sample Window" control. The level is displayed using a QProgressBar control
# with the value changed on the events of a main window QTimer object with a
# tick period that can be set using the "Meter Update Period" in the main
# window.
#
# The updates to and access to thread data are synchronized with a single
# QMutex object for all thread state requiring synchronized access.
#
# PyAudioMeter is free software: you can redistribute it and/or modify it under
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

from PySide6.QtCore import (QMutex, QThread, QLoggingCategory,
                            qCDebug, qCWarning, Signal)

import math

# Both numpy and scipy have real FFT functions. Their CPU load is high but numpy
# is much higher than scpipy, though the result looks to have nicer resolution.
# The rfft funcion in numpy and in scipy both provide Hermitian symmetric
# output, despite what the docs say. The result size/length is N when the number
# frequencies is (N / 2) + 1. So, we have to slice the output FFT bins in both
# cases.
import numpy as np
#from scipy.fft import rfft, rfftfreq
from scipy import signal

import pyaudio


class qtmAudioRxThread(QThread):
    '''
    Audio capture thread class. Performs monitoring of audio sample data and
    keeps a sum of sample absolute amplitudes and number of samples it
    represents. These are used to provide a mean amplitude on demand.
    FIXME: This might need nested locks if run() can overlap multiple calls for
           built-up data, e.g. counts not matching because we didn't lock around
           gathering the FFT data AND and number of combined elements in it.
    '''

    audioThreadLock = QMutex()
    showLocks = False

    audioDev = None
    stream = None

    endRun = False

    showBadFilterMessage = Signal(str)

    # Default audio parameters. Note that audio frame len can define latency in
    # attempts to read audio sample data, larger values take longer to supply.
    # 1024 samples per-frame at 44100kHz is a little under 1/50 seconds. Keep
    # the current numpy format updated so that we don't have to keep looking it
    # up
    FORMAT = pyaudio.paInt16
    sampleFormat = np.int16
    sampleLen = 2

    CHANNELS = 1
    RATE = 44100
    nyquistRate = int(44100 / 2)
    SAMPLE_FRAME_LEN = 1024
    lastRate = 0

    # Mean amplitude for each sample frame and sum of them
    sampleFrameAmplitudes = []
    nSampleFrameAmplitudes = 0
    sumSampleFrameAmplitudes = 0
    meanSampleFrames = 1

    sampleWindow = 0.25

    # FFT state

    # Duration in seconds of sample data used in a single FFT transformation. It
    # needs to be fairly long to capture the presence of many frequencies. If a
    # way of changing this appears it also needs to replace the window function
    tFFTUnit = 2.0

    # Let the user of the class supply a duration in seconds that is the length
    # of time for individual FFT displays, e.g. when drawing a FFT through the
    # day view how long is one display line or column, We use it to decide a
    # the number of FFTs to to batch sums of
    fftViewElementDuration = int(tFFTUnit)
    batchFFTDuration = int(2.0 * tFFTUnit)

    # The accumulating sample data over time, it doesn't need to be endless but
    # it does need to have enough for a few tFFTUnit counts
    sampleStream = None
    nSampleStream = 0

    # Length of the sample stream in units of length tFFTUnit
    fftFrameCount = 0

    # When we have data don't let it get shorter than this number of frames
    fftMinimumSampleFrame = 2

    # Next FFT frame to be transformed
    # fftAciveFrame = 0
    fftActiveStart = 0

    # Summed FFT data and number of summed elements
    fftSum = None
    accumFFTSums = 0

    # x-axis frequencies for bins
    xFreq = None
    lastBinCount = 0

    # Window overlap
    windowOverlapRatio = 0.66
    # windowOverlapRatio = 0.75

    # Window function name to use (default to Blackman-Harris"
    windowFn = "Blackman-Harris"

    # The actual window function
    fnWindow = None

    # A work-in-progress sample frame that is to be used by multiple functions
    # It must be populated, modified by the multiple functions and used within
    # a single object lock period
    frameSamples = None
    nFrameSamples = 0

    # The same as frameSamples but after applying a filter, the same rules
    # apply as for frameSamples.
    filteredSameples = None

    # Configuration for any enabled audio filter applied when making the
    # spectrum view. Among the uses of this is to filter out signal material at
    # frquencies with very high intensity audio so that more of the whole
    # spectrum detail is visible.
    filtType = ""
    filtLowF = 1
    filtHighF = 2
    filtOrder = 3

    # These are the actual filter
    filterA = None
    filterB = None

    logCategory = QLoggingCategory("QtMeter.Audio.Thread")

    def __show_lock(self, isLock=True):
        '''
        Show the line number identifying a lock/unlock request. Caller of this
        is not the location of the code requiring the lock action, those
        locations call dedicated private functions __lock() and __unlock(). This
        function is so that the show or not of lock diagnostics has one place of
        implementation. We get the line number two frames up the call stack and
        show it as the lock/unlock location.
        '''

        # Assumed call order is __lock() or __unlock() calls this and the caller
        # of those is the frame with the line number we care about
        lnum = sys._getframe(2).f_lineno

        if isLock is True:
            msg = "L"
        else:
            msg = "U"

        msg += " {}".format(lnum)
        qCDebug(self.logCategory, msg)

    # Don't use the lock object directly, provide accessor functions so that
    # the showing of the lock action in debug code can be included in the action
    # rather than a location dependent behavior.

    def __lock(self):
        '''
        Apply thread lock, if lock diagnosis is enabled (self.showLocks is True)
        call showLocks which displays the line number of it's frame 2 (this
        functions caller, frame 1) as the location the lock operation occurred
        at.
        '''

        # For lock and when lock diagnosis is enabled we show the request before
        # the lock operation so that deadlocks are visible
        if self.showLocks is True:
            self.__show_lock()
        self.audioThreadLock.lock()

    def __unlock(self):
        '''
        Release thread lock, caller supplies the line number of the call to
        permit display of lock actions taking place when that diagnostic is
        enabled.
        '''

        # For unlock and when lock diagnosis is enabled we show the request
        # after the lock operation so that deadlocks are visible
        self.audioThreadLock.unlock()
        if self.showLocks is True:
            self.__show_lock(False)

    @property
    def __audio_open(self):
        '''
        Return True if the instance has an audio device and an open sample
        stream
        '''

        return (self.audioDev is not None) and (self.stream is not None)

    def __start_audio(self):
        '''
        If there is no audio device open the default one and a sample stream
        '''

        if self.audioDev is None:
            self.audioDev = pyaudio.PyAudio()

            # Open a sample input stream from the audio device
            if self.FORMAT == pyaudio.paInt8:
                qCDebug(self.logCategory, "Starting 8-bit signed audio stream")
                # debug_message("Starting 8-bit signed audio stream")
            self.stream = self.audioDev.open(format=self.FORMAT,
                                             channels=self.CHANNELS,
                                             rate=self.RATE,
                                             input=True,
                                             frames_per_buffer=self.SAMPLE_FRAME_LEN)
            if self.stream is not None:
                qCDebug(self.logCategory, "Started audio, stream open")
                # debug_message("Started audio, stream open")

            # Reset sample tracking data
            self.__reset_stream_amplitude()

            # FIXME: Add back FFT support
            self.__preset_fft_state()

    def __stop_audio(self):
        '''
        If there is an open sample stream close it. If there is an open audio
        device close it.
        '''

        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.stream = None

        if self.audioDev is not None:
            self.audioDev.terminate()
        self.audioDev = None

    def end_meter(self):
        '''
        Causes the thread loop to stop, it will stop any started audio
        '''

        self.endRun = True

    @property
    def nyquist_frequency(self):
        '''
        We know the sample rate, provide the expected nyquist frequency when
        using it
        '''

        # return int(self.RATE / 2.0)
        return self.nyquistRate

    @property
    def sample_rate(self):
        '''
        Return the current sample rate
        '''

        return self.RATE

    def set_sample_rate(self, newRate):
        '''
        If audio is not already being monitored set the sample rate in Hz
        '''

        if not self.__audio_open:
            if self.RATE != newRate:
                self.RATE = newRate
                # Don't compute the Nyquist frequency every time we need it,
                # compute it only if we change the sample rate
                self.nyquistRate = int(newRate / 2)
                self.set_sample_window(self.sampleWindow)

            # Create a window function based on this rate even if we didn't
            # change the rate because the window function may have changed
            # without a new rate value
            self.__create_window_function()

    @property
    def sample_format(self):
        '''
        Return the audio sample format, e.g. pyaudio.paInt16
        '''

        return self.FORMAT

    def set_sample_size(self, newSize):
        '''
        Set the audio sample size, e.g. pyaudio.paInt16
        '''

        self.FORMAT = newSize
        self.__set_numpy_sample_format()
        self.__set_sample_len()
        self.__sample_peak()

    @property
    def mono_source(self):
        '''
        Return True if the number of audio channels is 1 (mono)
        '''

        return (self.CHANNELS == 1)

    def set_mono_source(self):
        '''
        Set the number of audio channels to 1 (mono)
        '''

        self.CHANNELS = 1

    @property
    def stereo_source(self):
        '''
        Return True if the number of audio channels is 2 (stereo)
        '''

        return (self.CHANNELS == 2)

    def set_stereo_source(self):
        '''
        Set the number of audio channels to 2 (stereo)
        '''

        self.CHANNELS = 2

    @property
    def channels(self):
        '''
        Return the number of audio channels to be sampled
        '''

        return self.CHANNELS

    def set_sample_frame_byte_len(self, newSize):
        '''
        Set the size of the audio sample data buffer in bytes
        '''

        self.SAMPLE_FRAME_LEN = int(newSize)

    def __set_numpy_sample_format(self):
        '''
        Return the size of an audio sample in numpy array size codes based on
        the pyaudio sample size code
        '''

        # These are oddly ordered but in likelihood of use to minimize execution
        # cost for the most used cases
        if self.FORMAT == pyaudio.paInt16:
            self.sampleFormat = np.int16
        # elif self.FORMAT == pyaudio.paInt24:
        #     sampleFormat = np.int24
        elif self.FORMAT == pyaudio.paInt32:
            self.sampleFormat = np.int32
        elif self.FORMAT == pyaudio.paFloat32:
            self.sampleFormat = np.float32
        elif self.FORMAT == pyaudio.paInt8:
            self.sampleFormat = np.int8
        else:
            # Assume 16-bit signed int by default
            self.sampleFormat = np.int16

    def __set_sample_len(self):
        '''
        Return the length of an audio sample in bytes
        '''

        if self.FORMAT == pyaudio.paInt16:
            self.sampleLen = 2
        elif self.FORMAT == pyaudio.paInt32:
            self.sampleLen = 4
        elif self.FORMAT == pyaudio.paFloat32:
            self.sampleLen = 4
        elif self.FORMAT == pyaudio.paInt8:
            self.sampleLen = 1
        # elif self.FORMAT == pyaudio.paInt24:
        #     sampleFormat = numpy.int24
        else:
            # Assume 16-bit signed int by default
            self.sampleLen = 2

    def __sample_peak(self):
        '''
        Return the peak possible value for an audio sample based on the pyaudio
        sample size. Largest minimum value for the same audio sample is negative
        the value obtained from this function.
        '''

        if self.FORMAT == pyaudio.paInt16:
            self.PEAK = 2 ** 15 - 1
        elif self.FORMAT == pyaudio.paInt32:
            self.PEAK = 2 ** 31 - 1
        elif self.FORMAT == pyaudio.paFloat32:
            max_exponent = 2.0 ** 23.0 - 1.0
            max_fraction = 2.0 ** -23.0 - 1.0
            self.PEAK = max_exponent + max_fraction
        elif self.FORMAT == pyaudio.paInt8:
            self.PEAK = 2 ** 7 - 1
        else:
            # Assume 16-bit signed int by default
            self.PEAK = 2 ** 15 - 1

        # Float format returns a float, int format returns an int
        return self.PEAK

    @property
    def sample_peak(self):
        return self.__sample_peak()

    @property
    def samples_per_frame(self):
        '''
        Use the "frame" (sample buffer) size and the length of a sample each in
        bytes, return the number of samples per chunk.
        '''

        # A sample is channel times sample length values
        return self.SAMPLE_FRAME_LEN / (1.0 * self.CHANNELS * self.sampleLen)

    @property
    def sample_frame_duration(self):
        '''
        Use the samples per-frame and the sample rate to return the duration
        of a sample frame in seconds.
        '''

        # How long does the chunk size we record contain samples for
        return self.samples_per_frame / self.RATE

    def mean_sample_frames_in_duration(self, duration):
        '''
        Return the number of frames that would have to be used to monitor
        audio samples for a given duration

        Parameters
        ----------
        duration: Floating point number
            A duration of time in seconds
        '''

        return round(duration / self.sample_frame_duration)

    def set_sample_window(self, newSampleWindow):
        '''
        Set the audio sample window size in seconds

        This is the number of mean levels for chunks that we can use to get a
        low and high value in a time-period

        Sets the number of audio sample frames required to access that duration

        Parameters
        ----------
            newSampleWindow: Floating point number
                The duration in seconds to use as the sample window

        '''

        # Do it with the object locked
        self.__lock()

        # Save the new sample window (seconds)
        self.sampleWindow = newSampleWindow

        # Our rolling mean is the ratio of the supplied sample window and the
        # duration of a sample frame.
        self.meanSampleFrames = self.mean_sample_frames_in_duration(newSampleWindow)

        # The rolling mean needs at least one entry
        if self.meanSampleFrames < 1:
            self.meanSampleFrames = 1
        # The rolling mean shouldn't be longer than about a second
        else:
            secondOfSampleFrames = self.mean_sample_frames_in_duration(1.0)
            if self.meanSampleFrames > secondOfSampleFrames:
                self.meanSampleFrames = secondOfSampleFrames

        # If there are no FFT chunks use the same as mean chunks
        # FIXME: FFT excluded for now
        if False is True:
            if self.fftChunks < 1:
                self.fftChunks = self.meanChunks

        # Finished
        self.__unlock()

    @property
    def __current_mean_amplitude(self):
        '''
        Return the mean amplitude of recorded sample data. Caller should hold
        the object lock. It's not done here so that you can get mean and max in
        the same lock window
        '''

        # If there is any sample data
        if self.nSampleFrameAmplitudes > 0:
            # The mean is sum divided by the count
            mAmp = self.sumSampleFrameAmplitudes / (1.0 * self.nSampleFrameAmplitudes)
        else:
            # No data, assume mean of 1.0
            mAmp = 1.0

        return mAmp

    @property
    def __current_max_amplitude(self):
        '''
        Return the maximum amplitude of recorded sample data. Caller should hold
        the object lock. It's not done here so that you can get mean and max in
        the same lock window
        '''

        # If there is any sample data
        if self.nSampleFrameAmplitudes > 0:
            # Get the maximum amplitude of signal amplitudes
            mAmp = np.max(self.sampleFrameAmplitudes)
        else:
            # No data, use the highest possible value
            # FIXME: Doesn't zero make more sense when there is no data?
            mAmp = self.PEAK

        return mAmp

    @property
    def current_dB(self):
        '''
        Return the mean amplitude in dB of recorded sample data relative to the
        peak sample value so that all cases have the same relation.

        The result is not a sound pressure level because it is relative to the
        peak value of samples and not relative to an ambient sound level in the
        environment.
        '''

        # Lock the set of sample data we test
        self.__lock()

        meanAmp = self.__current_mean_amplitude
        # maxAmp = self.__current_max_amplitude

        # No longer need unchanging sample data
        self.__unlock()

        peakAmp = self.PEAK
        # debug_message("dB from: {:.1f} / {}".format(mAmp, self.PEAK))
        if (meanAmp == 0.0) or (peakAmp == 0.0):
            # Zero would cause a ValueError from computing the signal level
            # ratio or from log10. Use the minimum value the meter can display.
            dBVal = -90
        else:
            # if (meanAmp < 0.001) or ((peakAmp < 0.001) and (peakAmp > -0.001)):
            #     qCDebug(self.logCategory, "dB mean: {}, peak {}".format(meanAmp, peakAmp))

            # Compute the dB value from the ratio of signal mean and max
            # possible so that all dB values are relative to the same value
            dBVal = 20.0 * math.log10(meanAmp / peakAmp)

        # Return the dB value (all are ratios of mean versus peak possible value
        # so that quiet signals aren't amplified relative to loud signals
        return dBVal

    def set_fft_view_duration(self, newDuration):
        '''
        Let the user of the class supply a duration in seconds that is the
        length of time for individual FFT displays, e.g. when drawing a FFT
        through the day view how long is one display line or column, We use it
        to decide the number of FFTs to do batch sums of
        '''

        # Be sure it's an integer and use a minimum
        self.fftViewElementDuration = int(newDuration)
        iMinDuration = int(2.0 * self.tFFTUnit)
        self.batchFFTDuration = int(self.fftViewElementDuration / 8)
        if self.batchFFTDuration < iMinDuration:
            # This should be impossible so warn!
            msg = "FFT batch durtion {} s ".format(self.batchFFTDuration)
            msg += "is shorter than FFT unit time {}s".format(self.tFFTUnit)
            qCDebug(self.logCategory, msg)

            self.fftViewElementDuration = iMinDuration
            self.batchFFTDuration = iMinDuration
            if iMinDuration > 1:
                self.batchFFTDuration -= 1

    @property
    def __fft_frame_size(self):
        fftFrameSize = int(self.tFFTUnit * self.RATE)
        if (fftFrameSize % 1) == 1:
            fftFrameSize + 1

        return fftFrameSize

    @property
    def frames_in_stream(self):
        fftFrameSize = self.__fft_frame_size
        if fftFrameSize != 0:
            result = int(self.nSampleStream / fftFrameSize)
        else:
            result = 0

        return result

    @property
    def fft_data(self):
        '''
        Return the current FFT frequency power bins data
        FIXME: We can't prevent this having data added after we obtain it and
               before we reset it...
        '''

        # fftFrameSize = self.__fft_frame_size

        self.__lock()

        # Update FFT, if necessary
        self.__do_FFT()

        result = self.fftSum

        # qCDebug(self.logCategory, "Returning {} accumulated FFTs".format(self.accumFFTSums))

        # No data exists now except the pre-samples we keep for window overlap
        # sliceFrom = fftFrameSize * self.fftMinimumSampleFrame
        # self.sampleStream = self.sampleStream[sliceFrom:]

        # Length of the sample stream in units of length tFFTUnit
        # fftFrameCount = self.fftMinimumSampleFrame

        # Next FFT frame to be transformed
        # fftAciveFrame = 0

        # Summed FFT data and number of summed elements are reset
        self.fftSum = None
        self.accumFFTSums = 0

        self.__unlock()

        return result

    @property
    def fft_freqs(self):
        '''
        Return the array listing the frequency covered by each bin in the FFT
        frequency data
        '''

        self.__lock()
        result = self.xFreq
        self.__unlock()

        return result

    def reset_FFT_data(self):
        '''
        Caller owns the time-domain and we sum FFT data between calls to this
        FIXME: It isn't safe to do this as a consequence of fft_data() without
               holding the object lock across both
        '''

        # For now do nothing...
        return

        self.__lock()

        self.latestFFT = None
        # self.lastFFTChunk = 0
        self.fftChunks = 0
        # self.activeChunk = 0
        self.sampleChunks = 0
        self.accumSums = 0

        # qCDebug(self.logCategory, "Reset FFT state")

        self.__unlock()

    def __capture_audio_sample_frame(self):
        '''
        Capture a frame of audio samples. Caller is responsible for knowing that
        self.__audio_open is True (an audio stream is open)
        '''

        # Capture a frame of audio samples
        try:
            data = self.stream.read(self.SAMPLE_FRAME_LEN)
            if data is not None:
                # Get a view of the data we can use numpy to perform
                # calculations on.
                sampleFrame = np.frombuffer(data, dtype=self.sampleFormat)

                # Return the frame
                return sampleFrame

        except IOError as e:
            msg = "Audio device read error: {}".format(e)
            qCWarning(self.logCategory, msg)

        # If we get here we didn't get a sample frame
        raise IOError

    def set_window_type(self, newType):
        self.windowFn = newType
        self.__create_window_function()

    #property
    def window_type(self):
        return self.windowFn

    def __get_window_function(self, windowName, sampleCount):
        '''
        Get a window function of a given type name for a given number of samples
        of audio data
        Parameters
        ----------
            windowName: Text string giving the name used in the Settings dialog
                        UI for the window function
            sampleCount: The number of samples the function is to be applied to

        Returns the window function
        '''

        if windowName == "Boxcar":
            fnWindow = signal.windows.boxcar(sampleCount)
        elif windowName == "Triangular":
            fnWindow = signal.windows.triang(sampleCount)
        elif windowName == "Blackman":
            fnWindow = signal.windows.blackman(sampleCount)
        elif windowName == "Hamming":
            fnWindow = signal.windows.hamming(sampleCount)
        elif windowName == "Hann":
            fnWindow = signal.windows.hann(sampleCount)
        elif windowName == "Bartlett":
            fnWindow = signal.windows.bartlett(sampleCount)
        elif windowName == "Flat top":
            fnWindow = signal.windows.flattop(sampleCount)
        elif windowName == "Parzen":
            fnWindow = signal.windows.parzen(sampleCount)
        elif windowName == "Bohman":
            fnWindow = signal.windows.bohman(sampleCount)
        elif windowName == "Blackman-Harris":
            fnWindow = signal.windows.blackmanharris(sampleCount)
        elif windowName == "Nuttall":
            fnWindow = signal.windows.nuttall(sampleCount)
        elif windowName == "Bartlett-Hann":
            fnWindow = signal.windows.barthann(sampleCount)
        elif windowName == "Cosine":
            fnWindow = signal.windows.cosine(sampleCount)
        elif windowName == "Exponential":
            fnWindow = signal.windows.exponential(sampleCount)
        elif windowName == "Tukey":
            fnWindow = signal.windows.tukey(sampleCount)
        elif windowName == "Taylor":
            fnWindow = signal.windows.taylor(sampleCount)
        elif windowName == "Lanczos":
            fnWindow = signal.windows.lanczos(sampleCount)
        else:
            # Unrecognized, assume no window
            qCDebug(self.logCategory, "Unrecognized window {}, size {}".format(windowName, sampleCount))
            fnWindow = None

        return fnWindow

    def __get_sp_filter_name(self):
        '''
        Get the scipy filter name from our own, human readable  name
        '''

        if self.filtType == "Low pass":
            filtName = "lowpass"
        elif self.filtType == "High pass":
            filtName = "hp"
        elif self.filtType == "Band pass":
            filtName = "bandpass"
        elif self.filtType == "Band stop":
            filtName = "bandstop"
        else:
            filtName = ""

        return filtName

    @property
    def filter_type(self):
        return self.filtType

    @property
    def filter_low_f(self):
        return self.filtLowF

    @property
    def filter_high_f(self):
        return self.filtHighF

    @property
    def filter_order(self):
        return self.filtOrder

    def set_filter_type(self, newType):
        if newType != self.filtType:
            self.filtType = newType
            self.__create_sample_filter()

    def set_filter_low_f(self, newLowF):
        if newLowF != self.filtLowF:
            self.filtLowF = newLowF
            self.__create_sample_filter()

    def set_filter_high_f(self, newHighF):
        if newHighF != self.filtHighF:
            self.filtHighF = newHighF
            self.__create_sample_filter()

    def set_filter_order(self, newOrder):
        if newOrder != self.filtOrder:
            self.filtOrder = newOrder
            self.__create_sample_filter()

    def __create_sample_filter(self):
        '''
        If we have a configured sample filter return it, this doesn't do the
        sample filtering. If a and b are both not None the caller is expected
        to use scipy.signal.filtfilt(), if a is not None and b is None the
        caller is expected to use scipy.signal.sosfilt(). If a and b are both
        None the signal should not be filtered. a is None and b is not None is
        undefined for the caller.
        '''

        # Do we need a filter
        a = None
        b = None

        self.__lock()

        if self.filtType != "":
            # qCDebug(self.logCategory, "Use filter: {}".format(self.filtType))

            # Get the scipy filter name to use
            filtName = self.__get_sp_filter_name()

            # Use the name to choose what to do. This requires a lot of care,
            # if a and b are not None the caller should do a signal.filtfilt()
            # but order of a and b matters. If a is not None and b is None the
            # caller should use a for signal.sosfilt().
            # FIXME: Improve this to allow filter model selection and other,
            #        filter attributes (e.g. order). Requires UI changes as
            #        well.
            if self.filtType == "Low pass":
                if (self.filtHighF > 0) and\
                        (self.filtHighF < self.nyquist_frequency):
                    a, b = signal.butter(self.filtOrder, self.filtHighF,
                                         btype=filtName)
            elif self.filtType == "High pass":
                if (self.filtLowF > 0) and\
                        (self.filtLowF < self.nyquist_frequency):
                    a = signal.butter(self.filtOrder, self.filtLowF,
                                      btype=filtName, fs=self.sample_rate,
                                      output='sos')
                    b = None
            elif self.filtType == "Band pass":
                if (self.filtLowF > 0) and\
                        (self.filtHighF <= self.nyquist_frequency) and\
                        (self.filtHighF > self.filtLowF):
                    fRange = [self.filtLowF, self.filtHighF]
                    a, b = signal.butter(self.filtOrder, fRange,
                                         btype=filtName,
                                         fs=self.sample_rate)
            elif self.filtType == "Band stop":
                if (self.filtLowF >= 0) and\
                        (self.filtHighF <= self.nyquist_frequency) and\
                        (self.filtHighF > self.filtLowF):
                    fRange = [self.filtLowF, self.filtHighF]
                    a, b = signal.butter(self.filtOrder, fRange,
                                         btype=filtName,
                                         fs=self.sample_rate)

        self.filterA = a
        self.filterB = b

        self.__unlock()

    def __drop_redundant_samples(self):
        '''
        Given the current position and minimum sample length for overlapped
        windowing, drop any used samples. Caller MUST hold object lock since we
        discarding sample data and adjusting positional state
        '''

        # How big is a FFT frame and the minimum number of frames in samples
        fftFrameSize = self.__fft_frame_size
        minimumSamples = self.fftMinimumSampleFrame * fftFrameSize

        # As long as we are longer than the minimum length we can discard
        # early frames
        if self.fftActiveStart > minimumSamples:
            # Frame count we can safely slice from the start
            sliceSamples = self.fftActiveStart - minimumSamples

            # msg = "Dropping {} indices".format(sliceSamples)
            # qCDebug(self.logCategory, msg)

            # We slice from the slice position to the end, but limit it to at
            # least one frame
            if sliceSamples >= fftFrameSize:
                tmpSlicedStream = self.sampleStream[sliceSamples:]
                self.sampleStream = tmpSlicedStream.copy()
                self.nSampleStream -= sliceSamples

                # We must update object counting and postioning data
                # newLength = self.sampleStream.size
                # self.fftFrameCount = int(newLength / fftFrameSize)
                self.fftFrameCount = int(self.nSampleStream / fftFrameSize)
                self.fftActiveStart -= sliceSamples

                # msg = "New FFT stream frame "
                # msg += "start {} ".format(self.fftActiveStart)
                # msg += "of ".format(self.fftFrameCount)
                # msg ++ "whole length {}".format(self.sampleStream.size)
                # qCDebug(self.logCategory, msg)

    def __get_frame_limits(self, overlapLength):
        '''
        Return the start, end and length of the next frame for __do_FFT().
        Although length is implied doing it here keeps it in it's own block.
        Caller should hold object lock to prevent critical values changing while
        being accessed/used.
        Parameters
        ----------
            overlapLength: Integer
                The length of overlapped samples to use in order to prevent
                windowing damping signal areas. The value must be smaller than
                the frame length
        '''

        # Get the size of a FFT frame
        fftFrameSize = self.__fft_frame_size

        # get the start and end sample and length for the frame we are at
        fftFrameStart = self.fftActiveStart - overlapLength
        if fftFrameStart < 0:
            fftFrameStart = 0
        fftFrameEnd = fftFrameStart + fftFrameSize
        fftFrameLen = fftFrameEnd - fftFrameStart

        # qCDebug(self.logCategory, "FFT stream positions {}..{}/{} ({}) whole length {}".format(fftFrameStart, fftFrameEnd, fftFrameLen, fftFrameEnd - fftFrameStart, fftFrameSize))

        # Don't do a partial frame
        if fftFrameLen < fftFrameSize:
            qCDebug(self.logCategory, "FFT end of data in frame {} {}..{}, {} of {}".format(fftFrameStart, fftFrameEnd, fftFrameLen, fftFrameSize))
            raise ValueError

        # Wait until there is enough for a window overlap
        if fftFrameStart < 0:
            qCDebug(self.logCategory, "FFT starts before data {}..{}, {} of {}".format(fftFrameStart, fftFrameEnd, fftFrameLen, fftFrameSize))
            raise ValueError

        return fftFrameStart, fftFrameEnd, fftFrameLen

    def __get_initial_frame_limits(self, overlapLength):
        '''
        Return a first pass start, end and length of the next frame for
        __do_FFT(). Although length is implied doing it here keeps it in it's
        own block. Caller should hold object lock to prevent critical values
        changing while being accessed/used.
        Parameters
        ----------
            overlapLength: Integer
                The length of overlapped samples to use in order to prevent
                windowing damping signal areas. The value must be smaller than
                the frame length
        '''

        # Get the size of a FFT frame
        fftFrameLen = self.__fft_frame_size
        fftFrameStart = self.fftActiveStart - overlapLength
        if fftFrameStart < 0:
            # Can't overlap from before the beginning
            fftFrameStart = 0
        fftFrameEnd = fftFrameStart + fftFrameLen

        # qCDebug(self.logCategory, "FFT stream positions {}..{}/{} ({}) whole length {}".format(fftFrameStart, fftFrameEnd, fftFrameLen, fftFrameEnd - fftFrameStart, fftFrameSize))

        return fftFrameStart, fftFrameEnd, fftFrameLen

    def __get_next_frame_limits(self, fftFrameStart, fftFrameLen,\
                                overlapLength):
        '''
        Return a subsequent pass start, end and length of the next frame for
        __do_FFT(). Caller should hold object lock to prevent critical values
        changing while being accessed/used.
        Parameters
        ----------
            fftFrameStart: Integer
                The previous frame start position
            fftFrameLen: Integer
                The frame length being used (start and length imply end)
            overlapLength: Integer
                The length of overlapped samples to use in order to prevent
                windowing damping signal areas. The value must be smaller than
                the frame length
        '''

        fftFrameStart += fftFrameLen - overlapLength
        fftFrameEnd = fftFrameStart + fftFrameLen

        self.fftActiveStart = fftFrameStart

        return fftFrameStart, fftFrameEnd

    def __create_window_function(self):
        '''
        Get the current class window function as class state.
        '''

        # Do it locked because we can do it while the audio is running
        self.__lock()

        # If there is a named window function to be applied
        if self.windowFn != "":
            # Get the size of a FFT frame
            fftFrameSize = self.__fft_frame_size

            # Get the current window function
            self.fnWindow = self.__get_window_function(self.windowFn,\
                                                       fftFrameSize)
        else:
            # No window
            self.fnWindow = None

        self.__unlock()

    def __apply_any_window_function(self):
        '''
        Apply the current class window function to the current class samples for
        FFT transform. Can only be used when the caller holds the object lock
        and even then only really during the same lock period where the samples
        were stripped and made class state. Use thread state for the sample data
        to avoid transferring large arrays in and out of the function. It's
        really just to reduce the complexity of the view of the _do__FFT()
        function by putting parts of it with a single purpose in their own
        functions
        '''

        try:
            # Apply any window.
            # FIXME: It would be nice to do this in it's own function but it
            #        would have o gather the window function afresh for
            #        every sample frame when it rarely changes between
            #        frames. We could pass the window fuction we already
            #        retrieved to make that work but the function can be
            #        large and we only do the following test and multiply
            if self.fnWindow is not None:
                self.frameSamples *= self.fnWindow
        except:
            msg = "Exception "
            # msg += "in window function {} ".format(self.frameSamples.size)
            msg += "in window function {} ".format(self.nFrameSamples)
            msg += "versus {}".format(self.fnWindow.size)
            qCDebug(self.logCategory, msg)
            raise

    def __verify_filtered_data(self):
        '''
        Look at the filtered data, if it has any nan/minnan values the filter
        probably has a cutoff too close to a band-edge for the sampling.
        '''

        filtMin = np.min(self.filteredSamples)
        filtMax = np.max(self.filteredSamples)

        if np.isnan(filtMin) or np.isnan(filtMax):
            # Set the message.
            msg = "The filter configured in the Settings dialog cannot be "
            msg += "applied, it results in invalid data that cannot be used "
            msg += "to obtain a spectrum. The most likely reason is that the "
            msg += "filter has a cut-off frequency that is too close to a band "
            msg += "edge, e.g. too close to zero or too close to the Nyquist "
            msg += "frequency for the sample-rate."

            # Emit the signal to show the QMessageBox in the main thread.
            self.showBadFilterMessage.emit(msg)

    def __apply_any_filter(self):
        '''
        Apply the current class filter to the current class samples for FFT
        transform. Can only be used when the caller holds the class lock and
        even then only really during the same lock period where the samples
        were stripped and made class state. If no filter is applied the
        filteredSamples member is still used to say we've passed this point.
        It's really just to reduce the complexity of the view of the _do__FFT()
        function by putting parts of it with a single purpose in their own
        functions
        '''

        try:
            # Do we have a filter configuration to apply? Caller must hold
            # audioThreadLock.
            if (self.filterA is not None) and (self.filterB is not None):
                self.filteredSamples = signal.filtfilt(self.filterA,
                                                       self.filterB,
                                                       self.frameSamples)
                self.__verify_filtered_data()
            elif (self.filterA is not None) and (self.filterB is None):
                self.filteredSamples = signal.sosfilt(self.filterA,
                                                      self.frameSamples)
                self.__verify_filtered_data()
            else:
                self.filteredSamples = self.frameSamples

            # Look at filtered samples, if we have any nan values the filter
            # probably has cutoff too close to the edge of the sample band
            # range
        except:
            qCDebug(self.logCategory, "Exception in filter")
            self.__verify_filtered_data()
            raise

    def __create_bin_frequency_data_for_FFT(self, fftBinCount):
        '''
        Build the list of bin frequencies for a FFT with a given bin count and
        made from samples with a given sample frequency
        '''

        # Only change the current self.xFreq if something that would cause it to
        # change is itself changed
        if (fftBinCount != self.lastBinCount) or (self.lastRate != self.RATE):
            try:
                self.xFreq = np.fft.rfftfreq(fftBinCount, 1.0 / self.RATE)
                self.lastRate = self.RATE
                self.lastBinCount = fftBinCount
            except:
                qCDebug(self.logCategory, "Exception in FFT frequency bin generation")
                raise

    def __do_FFT(self):
        '''
        Perform a FFT conversion of linear samples. Caller MUST hold
        object lock
        FIXME: This currently repeats previous work by going through the whole
               sample set every time it's operational. Modify it to only deal
               with new sample data.
        FIXME: There's some duplication here, e.g. fftFrameEnd
        '''

        # How big is a FFT frame, use it to calculate an overlap length when
        # we have a window function
        fftFrameSize = self.__fft_frame_size
        if self.fnWindow is None:
            # No window functiom, no overlap
            overlapLength = 0
        else:
            # Use a window overlap
            overlapLength = int(self.windowOverlapRatio * fftFrameSize)

        # FIXME: This uses lots of try/except blocks, including called functions
        #        in order to isolate any bug to one operation
        try:
            # get the start and end sample and length for the frame we
            # are at
            fftFrameStart, fftFrameEnd, fftFrameLen =\
                    self.__get_initial_frame_limits(overlapLength)
            # qCDebug(self.logCategory, "FFT stream frame {}..{}/{} ({}) whole length {}".format(fftFrameStart, fftFrameEnd, fftFrameLen, fftFrameEnd - fftFrameStart, self.sampleStream.size))

            # The total number of new samples and where we must end transforming
            nSamples = self.nSampleStream - self.fftActiveStart
            minimumSamples = self.fftMinimumSampleFrame * fftFrameSize
            transformEnd = nSamples - minimumSamples

            # If there is at least the minimum number of samples
            # qCDebug(self.logCategory, "Looping {} byte frames from {} to {} of ".format(fftFrameSize, transformStart, transformEnd, self.sampleStream.size))
            while fftFrameEnd < transformEnd:
                try:
                    # Get the frame
                    # qCDebug(self.logCategory, "FFT stream frame {}..{}/{} ({}) of {}".format(fftFrameStart, fftFrameEnd, fftFrameLen, fftFrameEnd - fftFrameStart, self.sampleStream.size))
                    self.frameSamples = self.sampleStream[fftFrameStart:fftFrameEnd]
                    self.nFrameSamples = fftFrameLen

                    # Apply window and filter if they exist
                    self.__apply_any_window_function()
                    self.__apply_any_filter()

                    try:
                        # FFT the windowed, filtered signal
                        tmpFFT = np.fft.rfft(self.filteredSamples,
                                             norm="backward")

                        # No longer need these, drop any cross-reference they have
                        # to sample data
                        self.filteredSamples = None
                        self.frameSamples = None
                        self.nFrameSamples = 0

                        if tmpFFT is None:
                            qCDebug(self.logCategory, "None FFT at start {}".format(fftStart))
                    except:
                        self.filteredSamples = None
                        self.frameSamples = None
                        self.nFrameSamples = 0
                        qCDebug(self.logCategory, "Exception in FFT")
                        raise

                    # Get the frequencies for FFT bins, it does it's own
                    # avoidance of repeating the arithmetic if the things that
                    # would have the same result as the last time
                    self.__create_bin_frequency_data_for_FFT(int(fftFrameLen / 2) + 1)

                    try:
                        # Use absolute FFT values
                        tmpFFT = np.abs(tmpFFT)
                        binMin = np.min(tmpFFT)
                        binMax = np.max(tmpFFT)
                    except:
                        qCDebug(self.logCategory, "Exception in trimming FFT state")
                        raise

                    try:
                        # Sum them (caller resets the sum when desired)
                        if self.accumFFTSums == 0:
                            self.fftSum = tmpFFT
                            self.accumFFTSums = 1
                        else:
                            self.fftSum += tmpFFT
                            self.accumFFTSums += 1

                        # Release state with references we are finished with
                        tmpFFT = None

                        # Finished a frame, move forward by a frame, it updates
                        # self.fftActiveStart
                        fftFrameStart, fftFrameEnd =\
                                self.__get_next_frame_limits(fftFrameStart,
                                                             fftFrameLen,
                                                             overlapLength)
                    except:
                        qCDebug(self.logCategory, "Exception in summing FFTs")
                        raise
                except:
                    # End the loop
                    break
        except ValueError:
            # Under-run or over-run, let it pass because we are capturing data
            # live. fftActiveStart won't change between iterations when this
            # happens
            msg = "Not enough sample data ({}) ".format(self.nSampleStream)
            msg += "to perform FFT yet"
            qCDebug(self.logCategory, msg)

        # New active frame position
        # msg = "NEXT FFT will start from {}".format(self.fftActiveStart)
        # qCDebug(self.logCategory, msg)

        # As long as we are longer than the minimum length we can discard
        # early frames. Let the function work it out
        self.__drop_redundant_samples()

    def __preset_fft_state(self):
        '''
        Initialize the sample stream for FFTs, the working positions in it, some
        zero value samples and the accumulated FFT data all to the zero state
        for a few frames at the beginning of time
        '''

        # Pre-create a couple of tFFTUnit lengths of zero samples. This
        # allows us to have better overlapping windows
        fftFrameSize = self.__fft_frame_size
        self.nSampleStream = self.fftMinimumSampleFrame * fftFrameSize
        self.sampleStream = np.zeros(self.nSampleStream)

        self.fftFrameCount = self.frames_in_stream

        # Nothing processed yet
        self.fftAciveFrame = 0

        # Don't drop sample data earlier than this frame number
        self.fftMinimumSampleFrame = 1

        self.yieldCurrentThread()

    def __add_fft_stream_samples(self, newSamples):
        '''
        Add newSamples to the sample stream and if it's getting long then
        perform FFTs. Caller MUST hold object lock
        '''

        # Concatenate the sample data to the stream we'll use for
        # computing FFTs
        self.sampleStream = np.concatenate( [ self.sampleStream, newSamples] )

        # New size in samples, time and FFT frames
        self.nSampleStream += newSamples.size
        tSamples = self.nSampleStream / self.RATE
        fftFrameSize = self.__fft_frame_size
        self.fftFrameCount = int(self.nSampleStream / fftFrameSize)

        # Push a FFT so far so that when it's needed it's mostly
        # prepared by this thread and there isn't a latency to the
        # caller needing FFT data. It also should mean we do it in
        # small numbers of frames with time gaps for better CPU
        # utilization

        # Don't do it every iteration, we are very likely drawing
        # single line spectrums every few minutes covering the
        # samples during those minutes but we sum many shorter
        # spectrums to avoid doing giant ones with tiny frequency
        # width bins. Adjust the whole via self.tFFTUnit or re-write

        # Duration of sample frames we have not yet transformed
        newSamples = self.nSampleStream - (self.tFFTUnit * self.fftAciveFrame)
        newFrames = int(newSamples / fftFrameSize)
        tNewFrameSamples = newFrames * fftFrameSize / self.RATE

        # Use the computed batch duraton for the duration of FFTs to perform
        # in batches
        tLimit = self.batchFFTDuration

        # Are we at or beyond that limit
        tStep = tNewFrameSamples - tLimit
        # msg = "Time step {} ".format(tStep)
        # msg += "with limit {}. ".format(tLimit)
        # msg += "Sample duration {}. ".format(tSamples)
        # qCDebug(self.logCategory, msg)
        if tStep > 0:
            # msg += "Performing FFT..."
            # qCDebug(self.logCategory, msg)
            self.__do_FFT()

    def __reset_stream_amplitude(self):
        '''
        When the stream is started we need to reset the sample tracking data
        in case we had previously been running and have current data
        '''
        self.sampleFrameAmplitudes = []
        self.nSampleFrameAmplitudes = 0
        self.sumSampleFrameAmplitudes = 0

    def __add_stream_amplitude(self, frameAmplitude):
        '''
        Add a new amplitude to the tracked amplitude data, keeping the length
        limited to the user configured audio window. Caller must hold the object
        lock.
        '''

        # If we have reached or exceeded the audio window, remove the oldest
        # entries from the sum and the list
        # FIXME: If the del happens a lot then slice might be faster
        while self.nSampleFrameAmplitudes >= self.meanSampleFrames:
            self.sumSampleFrameAmplitudes -= self.sampleFrameAmplitudes[0]
            del self.sampleFrameAmplitudes[0]
            self.nSampleFrameAmplitudes -= 1

        # Add the new amplitude to the list and sum
        self.sampleFrameAmplitudes.append(frameAmplitude)
        self.nSampleFrameAmplitudes += 1
        self.sumSampleFrameAmplitudes += frameAmplitude

    def run(self):
        '''
        Thread runtime entry point. Function contains several uses of sleep due
        to the multiple long duration operations on large data sets.
        FIXME: Find ways to reduce the overhead of running this
        '''

        self.__start_audio()
        if self.__audio_open:
            # We'll track some things that should not change or at least change
            # rarely in the loop so that we can reduce some math. Start with
            # invalid values to detect a difference from. There is a class
            # version of lastRate for the same purpose of detecting when RATE
            # changes but we need our own version because the class one can be
            # set equal to RATE in other places
            lastRate = 0
            lastSamplesPerFrame = 0

            # Keep a count since our last yield in the loop that runs until
            # asked to stop
            i = 0
            while not self.endRun:
                try:
                    capStart = time.time()
                    sampleFrame = self.__capture_audio_sample_frame()
                    if sampleFrame is not None:
                        # Get the magnitude of the samples and use it to get the
                        # mean, without the abs() we'd have a mean signal of
                        # about zero
                        # FIXME: this walks through the level data the way that
                        #        displaying FFT walks through the same data in
                        #        the frequency domain. Perhaps they can be
                        #        combined
                        # FIXME: Find a way to not do these two every loop
                        absFrame = np.abs(sampleFrame)
                        frameAmplitude = np.mean(absFrame)

                        # Protect access to updates of class state
                        self.__lock()

                        # Track the amplitudes as we cycle, limiting the number
                        # to enough to fill the audio window
                        self.__add_stream_amplitude(frameAmplitude)

                        # Track sample data. This will automatically perform FFT
                        # transforms when the untransformed sample stream is
                        # getting long
                        self.__add_fft_stream_samples(sampleFrame)

                        # End of protected updates
                        self.__unlock()

                        # Periodic yield outside of the lock but in the loop
                        # while handling sample data, we definately yielded if
                        # there was no sample data (IOError).
                        i += 1
                        # if i >= 3:
                        #     self.yieldCurrentThread()
                        #     i = 0
                except IOError:
                    # No data, yield allowing for received audio to queue
                    i = 0

                # Only compute the sleep time if anything used to compute it
                # changes
                curSamplesPerFrame = self.samples_per_frame
                if (curSamplesPerFrame != lastSamplesPerFrame) or \
                        (self.RATE != lastRate):
                    # Even at the fastest expected sample rate we are going
                    # to want to sleep for about 6ms, so do it in msleep. We
                    # get a fraction of a second from the division, we want
                    # integer milliseconds for the msleep argument
                    # FIXME: This doesn't account for the sample for
                    #        multiple channels having the same time
                    #        reference, i.e. mono would have the correct
                    #        time but stereo would be twice as long for no
                    #        purpose.
                    reUseSleepTime = 1 + int(1000.0 * curSamplesPerFrame / self.RATE)
                    lastSamplesPerFrame = curSamplesPerFrame
                    lastRate = self.RATE

                # Sleep the re-used time less this loop iteration's elapsed time
                # and if there is no time, yield every so often
                msSleep = reUseSleepTime - round(1000 * (time.time() - capStart))
                if msSleep > 0:
                    self.msleep(msSleep)
                else:
                    if i >= 3:
                        self.yieldCurrentThread()
                        i = 0

        # End of main run loop, stop the audio
        self.__stop_audio()
