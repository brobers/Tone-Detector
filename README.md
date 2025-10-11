# Tone-Detector
Fire Department Tone Detector, Audio Recorder, and Paging Repeater

The Tone-Detector is a solution to an old and failing hardware solution used by a fire department I volunteer for.

Issue: Our fire department serves two counties. The fire deprtment operates on one VHF frequency used by the primary county where the fire department is located. The second county operates on a different VHF frequency. The second county did not in years past have the ability to add a second frequency to their console. Also the second counties transmitter is 15+ miles away from fire department members making reliable reception difficult to Motorola paging devices. As a solution a hardware solution was created at the fire department station consisting of a Motorola radio as a receiver only (on the second counties frequency), an outdated and no unavailable tone decoder circuit board, a prototye perf board with a small homemade circuit, simplexor repeater, a tone encoder, and a base radio on the primary county VHF frequency.

How it works: The secondary county, on their frequency would set off a two-tone paging pair for the fire department (not the same pair used for the fire department on the primary frequency). The encoder would receive the tone and activate the homemade circuit wired to the paging encoder at the fire department. This would send out the primary tones on the primary frequency from the fire department activating the pagers. The circuit would also activate the simplexor repeater and capture the next 30 seconds of audio on the secondary county frequency. At the end of recording the simplexor would key the radio and transmit the audio to the base radio on the primary frequency two times before resetting.

The problem: The system has over the years become flakey and fails to work, works normal, or will not play correctly (often many times more than 2 or with sever delay in playing). The tone detector board while commercial is now out of production and the homemade circuit was made by members of the local Motorola shop who have since retired. I am the only person left who understands the whole system in detail. There has to be a better way.

For many years I operated a Two-Tone-Detect Raspberry Pi unit that would detect tones from a scanner, record the audio, and send e-mail/SMS to members of our department prior to the emergence of Motorola pager having record and replay abilities. In time the author of Two-Tone-Detect had his freeware solution bought and it became a part of the IamResponding commercial platform. I have moved my solution to this platform as well and capture tones from multiple departments in both counties and submit them to IamResponding as our primary county provides this solution to our Fire/EMS agencies. While the original Two-Tone-Detect had some options to perform external commands after receiving tones I felt a better solution to our current setup was a better option than trying to adapt the IamResponding solution.

The solution: What comes now is a program called Tone-Detector. This is meant to be a simpler solution to the homemade circuit, simplexor, and use of the paging encoder. It is designed to do the following task:

-Listen for first tone.
-Listen for second tone and if not heard return to listening for the second tone.
-If both tones heard pause before recording audio on secondary radio for a defined time.
-Generate and transmite the fire department primary two-tone pattern
-Pause for a defined time to allow alerting on pager to complete.
-Play the recorded audio.
-Repreat the tones and the recorded audio pattern a second time and then return to listening for the first tone.

The program uses a JSON file for configuration data allowing the script to be adapted to other fire departments or to adjust for tolerance in tone and timing. Additionally being based on a Raspberry Pi the solution utilizes output pins to activate keydown on the primary department radio before playing back the audio.

v1.3 is the most current working version. It stores the audio files in the directory audio_files and log files in the directory log_files as a subdirectory of where the application is ran from.
