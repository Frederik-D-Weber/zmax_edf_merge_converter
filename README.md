## zmax_edf_merge_converter
Comprehensive conversion of a folder with Hypnodyne zmax (wearable) EDF files (originally convered using Hypondyne HDRecorder.exe) into a merged European Data Format .EDF (EDF+)
- after conversion lets you open the EDF file also in other software (because there are often header issues with some channels in the converted .edf files from HDRecorder)
- without refiltering the original EDFs
- can use the PPGParser.exe to get heart rate infos and cleaner PARSED signals
- can use the HDReceroder.exe to directly convert from .hyp files from the microSD card recordings.
- can use the EDFCleaner.exe to clean the signal from micro SD noise (mainly in the EEG channels at Harmonics of 85.33 Hz if electrode impedance is low/resistance is high).
- can use the EDFjoin.exe to directly convert join EDFs created by using HDReceroder.exe
- can read zipped ZMax EDF files
- can write zipped and merged/integrated EDF files
- can reduce the channel set to only the ones supported by the 'lite' version of the ZMax wearable
- exclude channels that are empty or flat (to save space)
- choose complete folder structures and work in place or export in another copy of the file structure without risk of overwriting
- choose if you want to overwrite files
- exclude and include file names in a complex file and folder structure
- write safe, i.e. only final files are written out (and overwritten, ... handy for restarting the process on a lot of files), files are written out with a temporary name in a safe location as to not overwrite unintenionally other files right until requested or have "half converted/written" files.
- find duplicates in the ZMax signals and/or files (or duration of the recording, also across different use of HDRecorder versions)

### REQUIREMENTS:
RUN it: Windows 7 and above, x64, to run the zmax_edf_merge_converter.exe
DEVELOP: python 3.8.9 or above (for compiling and coding)

### TESTED ON:
Windows 7, x64, python 3.8.9

### INSTALLATION:
Download the distribution zmax_edf_merge_converter.exe from the repository and see USAGE below
If you want to uses the PPGparser.exe of HDRecorder.exe to correct some nasal and PPG signals and generate the hear rate signal(s)
also install the Hypnodyne software suite found in http://hypnodynecorp.com/downloads.php or put the zmax_edf_merge_converter.exe into the same folder.

### KNOWN ISSUES:
 - Note that using the --zmax_edfjoin switch of this converter will utilize the EDFJoin.exe from the Hypnodyne Corp. ZMax Software Suite.
However as of version 2022-08-07 of this ZMax Software Suite, it failed to merge the EDFs signals correctly (the signals seemed scattered and unusable) in test on previous recorded data (also newly converted from .hyp).
Until this is fixed I would recommend to not use it.
- Legacy .EDF files (i.e. converted by HDRecorder.exe from versions prior to Hypnodyne Corp. ZMax Software Suite version 2022-08-07) have header issues in the 'BODY TEMP.edf' and 'BATT.edf' to properly open with other EDF tools. (this is handled by this software to create correct merged files)

### USAGE:
Note that using the default values you can also just drag-and-drop (e.g. in windows explorer) multiple folders and/or zipped ZMax edf files (i.e. the ones that HDRecorder.exe creates, but in a zip file) onto the
zmax_edf_merge_converter.exe (it will then run it using the default values).

It will also create a summary file called zmax_edf_merge_converter_summary_XXXXXXXX-XXXXXXXXXXXX.csv (where all the X will give the date and time of the run) that includes all the processed files and hash values to check for duplicate files.
If the duplicate finding was not completed (e.g. the program was terminated earlier, then you can just drag and drop the zmax_edf_merge_converter_summary_XXXXXXXX-XXXXXXXXXXXX.csv on the zmax_edf_merge_converter.exe to get those columns.

If you want to convert directly fron .hyp files of the microSD card, please copy them first to another location (e.g. your hard drive) and give the containing folder a proper designation (e.g. the subject number or date etc.).

It is recommended to have the ZMax Software Suite from Hypnodyne Corp. installed (https://hypnodynecorp.com/downloads.php)[https://hypnodynecorp.com/downloads.php] to take use of the HDRecorder.exe and the PPGParser.exe from the installation.
It is easiest to copy the zmax_edf_merge_converter.exe into the installation folder of the Software Suite from Hypnodyne Corp (e.g. have it copied to the "C:\Program Files (x86)\Hypnodyne\ZMax" folder, depending on the installation path of the Software Suite).

```
usage: zmax_edf_merge_converter.exe [-h]
                                    [--write_redirection_path WRITE_REDIRECTION_PATH]
                                    [--read_zip]
                                    [--zipfile_match_string ZIPFILE_MATCH_STRING]
                                    [--zipfile_nonmatch_string ZIPFILE_NONMATCH_STRING]
                                    [--zmax_ppgparser]
                                    [--zmax_ppgparser_exe_path ZMAX_PPGPARSER_EXE_PATH]
                                    [--zmax_ppgparser_timeout_seconds ZMAX_PPGPARSER_TIMEOUT_SECONDS]
                                    [--zmax_edfjoin]
                                    [--zmax_edfjoin_exe_path ZMAX_EDFJOIN_EXE_PATH]
                                    [--zmax_edfjoin_timeout_seconds ZMAX_EDFJOIN_TIMEOUT_SECONDS]
                                    [--zmax_eegcleaner]
                                    [--zmax_eegcleaner_exe_path ZMAX_EEGCLEANER_EXE_PATH]
                                    [--zmax_eegcleaner_timeout_seconds ZMAX_EEGCLEANER_TIMEOUT_SECONDS]
                                    [--zmax_raw_hyp_file]
                                    [--zmax_hdrecorder_exe_path ZMAX_HDRECORDER_EXE_PATH]
                                    [--zmax_hdrecorder_timeout_seconds ZMAX_HDRECORDER_TIMEOUT_SECONDS]
                                    [--zmax_raw_hyp_keep_edf]
                                    [--write_name_postfix WRITE_NAME_POSTFIX]
                                    [--temp_file_postfix TEMP_FILE_POSTFIX]
                                    [--resample_Hz RESAMPLE_HZ] [--zmax_lite]
                                    [--read_only_EEG] [--read_only_EEG_BATT]
                                    [--no_write] [--no_overwrite]
                                    [--no_summary_csv] [--no_file_hashing]
                                    [--no_signal_hashing]
                                    [--exclude_empty_channels] [--write_zip]
                                    parent_dir_paths [parent_dir_paths ...]

This is useful software to reuse EDF from zmax to repackage the original
exported EDFs and reparse them if necessary or zip them. Copyright 2022,
Frederik D. Weber

positional arguments:
  parent_dir_paths      A path or multiple paths to the parent folder where
                        the data is stored and converted from (and by default
                        also converted to)

optional arguments:
  -h, --help            show this help message and exit
  --write_redirection_path WRITE_REDIRECTION_PATH
                        An optional path to redirect writing to a different
                        parent folder (so to not accidentally overwrite other
                        files). Original folder structure is keept in the
                        subfolders.
  --read_zip            Switch to indicate if the input edfs are zipped and
                        end with .zip
  --zipfile_match_string ZIPFILE_MATCH_STRING
                        An optional string to match the name of the zip files
                        to search for. Use the pipe to separate different
                        search/match strings, e.g.
                        --zipfile_match_string="this|that" will search for
                        "this" and then for "that". If parent_dir_paths
                        contains direct paths to .zip files this does not
                        apply.
  --zipfile_nonmatch_string ZIPFILE_NONMATCH_STRING
                        An optional string to NOT match (i.e. exclude or
                        filter out) after all the zipfile_match_string zip
                        files have been found. Use the pipe to separate
                        different search/match strings, e.g.
                        --zipfile_nonmatch_string="this|that" will search for
                        "this" and then for "that". If parent_dir_paths
                        contains direct paths to .zip files this does not
                        apply.
  --zmax_ppgparser      Switch to indicate if ZMax PPGParser.exe is used to
                        reparse some heart rate related channels. you also
                        need to specify zmax_ppgparser_exe_path if it is not
                        already in the current directory. This will take time
                        to reprocess each data.
  --zmax_ppgparser_exe_path ZMAX_PPGPARSER_EXE_PATH
                        direct and full path to the ZMax PPGParser.exe in the
                        Hypnodyne ZMax software folder
  --zmax_ppgparser_timeout_seconds ZMAX_PPGPARSER_TIMEOUT_SECONDS
                        An optional timeout to run the ZMax PPGParser.exe in
                        seconds. If empty no timeout is used
  --zmax_edfjoin        Switch to indicate if ZMax EDFJoin.exe is used to
                        merge the converted ZMax EDF files. you also need to
                        specify zmax_edfjoin_exe_path if it is not already in
                        the current directory. This will take time to
                        reprocess each data. Note that this will disable
                        resampling or cleaning of empty channels or some skip
                        some values in an entry of the summary csv
  --zmax_edfjoin_exe_path ZMAX_EDFJOIN_EXE_PATH
                        direct and full path to the ZMax EDFJoin.exe in the
                        Hypnodyne ZMax software folder
  --zmax_edfjoin_timeout_seconds ZMAX_EDFJOIN_TIMEOUT_SECONDS
                        An optional timeout to run the ZMax EDFJoin.exe in
                        seconds. If empty no timeout is used
  --zmax_eegcleaner     Switch to indicate if ZMax EDFCleaner.exe is used to
                        clean the EEG channels from SD-card writing noise in
                        85.33 Hz and higher and lower harmonics (e.g. 42.66,
                        21.33, 10.66, 5.33 Hz...) you also need to specify
                        zmax_eegcleaner_exe_path if it is not already in the
                        current directory. This will take time to reprocess
                        each data.
  --zmax_eegcleaner_exe_path ZMAX_EEGCLEANER_EXE_PATH
                        direct and full path to the ZMax EDFCleaner.exe in the
                        Hypnodyne ZMax software folder
  --zmax_eegcleaner_timeout_seconds ZMAX_EEGCLEANER_TIMEOUT_SECONDS
                        An optional timeout to run the ZMax EDFCleaner.exe in
                        seconds. If empty no timeout is used
  --zmax_raw_hyp_file   Switch to indicate if ZMax HDRecorder.exe is used to
                        convert from .hyp files moved from the SD card. you
                        need to specify zmax_hdrecorder_exe_path if it is not
                        already in the current directory. This will take time
                        to reprocess each data.
  --zmax_hdrecorder_exe_path ZMAX_HDRECORDER_EXE_PATH
                        direct and full path to the ZMax HDRecorder.exe in the
                        Hypnodyne ZMax software folder
  --zmax_hdrecorder_timeout_seconds ZMAX_HDRECORDER_TIMEOUT_SECONDS
                        An optional timeout to run the ZMax HDRecorder.exe in
                        seconds. If empty no timeout is used
  --zmax_raw_hyp_keep_edf
                        Switch to indicate if after conversion with ZMax
                        HDRecorder.exe from .hyp files also the converted .edf
                        files in the subfolders should be kept. Note, this
                        wont apply for zipped .hyp files.
  --write_name_postfix WRITE_NAME_POSTFIX
                        file name post fix for the written files or
                        directories. Default is "_merged"
  --temp_file_postfix TEMP_FILE_POSTFIX
                        file name post fix for the written files or
                        directories that are not completely written yet.
                        Default is "_TEMP_"
  --resample_Hz RESAMPLE_HZ
                        An optional resample frequency for the written EDF
                        data.
  --zmax_lite           Switch to indicate if the device is a ZMax lite
                        version and not all channels have to be included
  --read_only_EEG       Switch to indicate if only "EEG L" and "EEG R"
                        channels should be read in. --zmax_lite switch is
                        invalidated by this
  --read_only_EEG_BATT  Switch to indicate if only "EEG L" and "EEG R" and
                        "BATT" channels should be read in. --zmax_lite switch
                        and --read_only_EEG is invalidated by this
  --no_write            Switch to indicate if files should be written out or
                        not.
  --no_overwrite        Switch to indicate if files should be overwritten if
                        existent
  --no_summary_csv      Switch to indicate if a summary file should not be
                        written
  --no_file_hashing     Switch to indicate if the file hash (i.e. MD5 sum)
                        should be calculated (to compare if data is the same
                        for same hash)
  --no_signal_hashing   Switch to indicate if the signal data hash should be
                        calculated (to compare if data is the same for same
                        hash)
  --exclude_empty_channels
                        Switch to indicate if channels that are constant (i.e.
                        empty and likely not recorded) should be
                        excluded/dropped. Requires some more computation time
                        but saves space in case it is not zipped.
  --write_zip           Switch to indicate if the output edfs should be zipped
                        in one .zip file
```
EXAMPLES:
```
zmax_edf_merge_converter.exe "C:\my\zmax\files\are\in\subfolders\here"
zmax_edf_merge_converter.exe "C:\my\zmax\files\are\in\subfolders\here" "C:\my\zmax\files\are\in\subfolders\andhere" "C:\my\zmax\files\are\in\subfolders\andthis.zip"
zmax_edf_merge_converter.exe "C:\my\zmax\files\are\in\subfolders\here" --zmax_lite --write_zip --read_zip
zmax_edf_merge_converter.exe "C:\my\zmax\files\are\in\subfolders\here" --zmax_ppgparser --zmax_ppgparser_exe_path="C:\Program Files (x86)\Hypnodyne\ZMax\PPGParser.exe"  --zmax_ppgparser_timeout=1000
zmax_edf_merge_converter.exe "C:\my\zmax\files\are\in\subfolders\here" --write_zip --exclude_empty_channels --zmax_ppgparser --zmax_ppgparser_exe_path="C:\Program Files (x86)\Hypnodyne\ZMax\PPGParser.exe"  --zmax_ppgparser_timeout=1000
zmax_edf_merge_converter.exe "C:\my\zmax\files\are\in\subfolders\here" --write_redirection_path="C:\and\shall\be\written\here\with\original\folder\structure" --write_zip --exclude_empty_channels --zmax_ppgparser --zmax_ppgparser_exe_path="C:\Program Files (x86)\Hypnodyne\ZMax\PPGParser.exe"  --zmax_ppgparser_timeout=1000
zmax_edf_merge_converter.exe "C:\my\zmax\files\are\in\subfolders\here" --write_redirection_path="C:\and\shall\be\written\here\with\original\folder\structure" --no_overwrite --temp_file_postfix="_TEMP_" --zipfile_match_string="_wrb_zmx_" --zipfile_nonmatch_string="_merged|_raw| - empty|_TEMP_" --exclude_empty_channels --zmax_lite --read_zip --write_zip --zmax_ppgparser --zmax_ppgparser_exe_path="C:\Program Files (x86)\Hypnodyne\ZMax\PPGParser.exe" --zmax_ppgparser_timeout=1000
```

### CHECKING OF RESULTS
To check the merged files use EDFbrowser from https://www.teuniz.net/edfbrowser/
Some analysis on merged EDFs can be done using https://github.com/Frederik-D-Weber/sleeptrip or https://raphaelvallat.com/yasa/build/html/index.html
LibreOffice (Calc) http://www.libreoffice.org/ can be used for opening the summary files and convert to Excel files if necessary.

### DUPLICATES

Backdrop for ZMax duplicates:
Some ZMax recordings on the microSD cards could be old recordings that have not been overwritten after last initialization but were nevertheless converted.
For example one subject has recorded 5 nights in the first 5 slots (i.e. the first 5 .hyp files on the microSD card are recorded with those nights), the card has been then re-initalized for the next subject, but the next subject only has 4 recordings.
Thus the slot number 5 can in some cicumstances still contain the data from the previous subject and can be a false duplicate of an inexistent 5th night recording of the second subject.
Thus there can be  duplicates in the data of a study.
There could be different kind of duplicates in the files:
(1) File duplicates (same size and md5 hash)
(2) Signal duplicates (same signals, even though the time of recording is different or it was a "wrong conversion" from another subject, e.g. from another slot at the SD card)
Unfortunately it seems that different versions of the HDRecroder also produce different versions of the Signal that are hard to detect. But those cases could maybe caught by potential (3) Recording duration duplicates that are the same in recording duration (and close recording dates) or exactly 5 seconds different (as this seems to be the case in a few tests I did).
(4) There could be duplicates in case the first three cases are not clear. Then one can take a look at the battery level at the end, and consider the recording dates of duplicates.

Understanding the results of the summary file for duplicates:
The resulting zmax_edf_merge_converter_summary_XXXXXXXX-XXXXXXXXXXXX.csv should contain some columns to help find duplicates manually:
1. file_number: the number to the file (like an ID for that file and a reference to the duplicates, see below). This helps to check how many files have been processed.
2. zmax_file_path_original: that is the path to the actual file that is checked
3. rec_start_datetime: start of recording as a date time (useful for checking which one of the duplicates "happened" first)
4. rec_stop_datetime: stop of recording as a date time
5. hash_zmax_file_path_original_md5: the hash that is unique for that file mentioned in zmax_file_path_original
6. rec_duration_seconds: the duration of the recordings (duplicates should have the same duration or exactly 5 s  more/less if it was converted with different Hypnodyne HDRecorder versions.)
7. rec_battery_at_end_voltage: the voltage at the last second of the recording. This might be a unique value, and duplicates might have similar voltage at the end.
8. hash_signals_before_conversion: THIS IS THE MOST IMPORTANT IN MY VIEW. Contains the hash of the actual signals. If the HDRecorder software was the same, and the PC on which it was converted, then it will show duplicates here if the hash is the same between different files.

... Then if the automatic post processing worked there should also be (if not just drag and drop the created zmax_edf_merge_converter_summary_XXXXXXXX-XXXXXXXXXXX.csv file on the zmax_edf_merge_converter_hbs_duplicates.exe to recreate from what is in there. However in this case it might not have checked all available files and terminated early.)
But then these columns should also be included which directly suggest the various types of duplicates:

9. duplicates_in_duration: it will list the (first) file_number that has the same duration with this one (otherwise empty)
10. duplicates_in_duration_different_conversion: it will list the file_number that has the same duration +5 seconds with this one (otherwise empty)
11. duplicates_in_hash_zmax_file_path_original_md5: it will list the file_number that has the same file hash with this one (otherwise empty)
12.duplicates_in_hash_signals_before_conversion: THIS IS THE MOST IMPORTANT IN MY VIEW. it will list the file_number that has the same signal hash with this one (otherwise empty)

... All the other columns in between are not relevant for finding duplicates typically, so don't be confused.

Suggestion how to use the summary results for finding duplicates:
Open in a spreadsheet program of your choice (e.g. Libre Office Calc). Look at the last columns.
If you find any (file) numbers in the "duplicates_in_XXXX" columns this might be your duplicates. Note that finding out which is the original can only come by examining the other info as well.
I think if there is a duplicates_in_hash_signals_before_conversion ...or... duplicates_in_hash_zmax_file_path_original_md5, it is definitely a duplicate.
If it is duplicates_in_duration ... or ... duplicates_in_duration_different_conversion it maybe just coincidence and looking at the rec_battery_at_end_voltage (if it is also very similar) or looking at the recording dates with the potential duplicates can help to get more clarity.
Would be nice if you have a few examples that you know are duplicates.
If this does not work, we might need to think of a more complicated approach.