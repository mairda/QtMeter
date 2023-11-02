# QtMeter
A Qt based live audio meter with day level and spectrum history views

Using python 3(.11) and Qt PySide 6 (6.6) create a dialog based application to
allow monitoring of the default audio device and display an audio level meter.
It almost certainly works with lower versions of the components than stated.

Controls are provided for:

* selecting a meter update rate as a frequency or time between updates
* for the amount of sample data (window) to be used in each displayed level
* linking the update rate and sample window
* selecting the audio sample frequency, bits per-sample and channels
* starting and stopping monitoring
* adjusting application settings

As well as a meter showing current sample level there are also views of the
signal minimum and maximum over time and the signal spectrum over time. The
duration used for both is one day and both view backgrounds are drawn in a
style that represents the time of day horizontally. The signal minimum and
maximum are shown by default in green and red respectively and the signal
spectrum is shown in yellow, though these can be changed in the settings dialog.

The maximum/minimum/spectrum are tracked for the time represented by consecutive
horizontal pixels in the view. That should be just under three minutes for each.
As one is drawn, it's running state is reset and new data recorded for the next
horizontal position. The spectrum is the mean of spectrum data in each period
and is displayed vertically with the lowest frequency at the top downwards
towards the highest (Nyquist) frequency at the bottom. The frequency scale is
linear and the strength of signal at each frequency is drawn in the transparency
of the spectrum color (default is yellow). Currently, the majority of energy is
found in the very low frequencies and there is very little visible detail in
common background audio, although an audio signal generator can be used to "see"
it is audio spectrum so any bad background lasting more than a couple of minutes
at relatively constant frequencies would be seen. I'm working on ways to bring
out more spectrum detail but of the handful of approaches tried so far none have
been effective. When filled, both these graphs effectively scroll to the left by
one eigth of a day to create clear space on the right to draw on.

Use by placing at least the .py files in a directory and launch by running the
python 3.11 program in the created directory with qtmeter.py as an argument,
e.g.:

> mkdir /home/myuser/QtMeter
> cp Download/*py /home/myuser/QtMeter/
> cd /home/myuser/QtMeter
> python3.11 ./qtmeter.py

Use the settings to specify your latitude and longitude so that the long-term
audio level data has a background that represents the day where you are
monitoring. If you press OK in the settings dialog the latitude/longitude are
saved and will be used when you reload the program.

Note that no reference audio level is available unless you know the value to
add in your own case so the apparent dB level displayed by the meter is NOT a
Sound Pressure Level and is only a self-relative dB value.

System audio management software should permit changing the default audio device
and that should be used to change the device that QtMeter monitors.

You can change the audio sampling configuration but the controls are populated
with standard values so any sound device that doesn't support chosen sampling
settings will not operate when the Start button is pushed. Equally, any sampling
settings a device supports that are not shown in the UI will not be usable to
monitor audio.

Required libraries include (minimum recommended version to use):

* PySide6 (6.6)
* pyaudio (0.2.11)
* numpy (1.25.2)
* scipy (1.11.1)

Their dependencies are also required but that should be ensured if you use an
automated python module installer like pip. Some variation around the stated
versions will probably be fully functional.

Others may be required for specific audio devices to work as a source.

For further development place all project files in a working directory. Qt
Creator can be used via the project file QtMeter.pyproject and dialog content
can be modified via the .ui files. If changes are made to the .ui files the
python representation of them should be re-built using a Qt User Interface
Compiler version 6, e.g.:

> uic-qt6 -o dlgQtMeter.py -g python qtmeter.ui
> uic-qt6 -o dlgQtMSettings.py -g python qtmSettings.ui

An other approach is to open any .ui file in a recent version of Qt Designer,
e.g. 6.6.0, where the menu option Form->View Python Code will show the compiled
version that can then be saved in a suitable existing or new .py file in the
project files.

As-of July 2023 the intended target platform is linux.
