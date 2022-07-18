## zmax_edf_merge_converter
conversion of a folder with Hypnodyne zmax (wearable) EDF files (originally convered using Hypondyne HDRecorder.exe) into a merged European Data Format .EDF (EDF+)
- lets you open the EDF file also in other software (because there are often header issues with some channels in the converted .edf files from HDRecorder)
- without refiltering
- can read zipped zmax files
- can write zipped EDF files
- can reduce the channel set to only the ones supported by the light/lite version of the zmax wearable

### REQUIREMENTS:
python3.8

### TESTED ON:
Windows 7, x64

### INSTALLATION:
```
Download the distribution zmax_edf_merge_converter.exe from the repository and see USAGE below
If you want to uses the PPGparser to correct some nasal and PPG signals and generate the hear rate signal(s)
also install the Hypnodyne software suite found in http://hypnodynecorp.com/downloads.php
```

### USAGE:
```
usage: zmax_edf_merge_converter.exe [-h]
                                    [--write_redirection_path WRITE_REDIRECTION_PATH]
                                    [--read_zip]
                                    [--zipfile_match_string ZIPFILE_MATCH_STRING]
                                    [--zipfile_nonmatch_string ZIPFILE_NONMATCH_STRING]
                                    [--zmax_ppgparser]
                                    [--zmax_ppgparser_exe_path ZMAX_PPGPARSER_EXE_PATH]
                                    [--zmax_ppgparser_timeout ZMAX_PPGPARSER_TIMEOUT]
                                    [--zmax_lite] [--exclude_empty_channels]
                                    [--write_zip]
                                    parent_dir_path

This is useful software to reuse EDF from zmax to repackage the original
exported EDFs and reparse them if necessary or zip them. Copyright 2022,
Frederik D. Weber

positional arguments:
  parent_dir_path       A path to the parent folder where the data is stored
                        and to be initialized

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
                        An optional string to match the name of the zipfiles
                        to search for using internal glob function
  --zipfile_nonmatch_string ZIPFILE_NONMATCH_STRING
                        An optional string to NOT match (i.e. exclude or
                        filter out) after all the zipfile_match_string
                        zipfiles ones have been found
  --zmax_ppgparser      Switch to indicate if ZMax PPGParser.exe is used to
                        reparse some heart rate related channels. you also
                        need to specify zmax_ppgparser_exe_path if it is not
                        already in the current directory. This will take time
                        to reprocess each data.
  --zmax_ppgparser_exe_path ZMAX_PPGPARSER_EXE_PATH
                        direct and full path to the ZMax PPGParser.exe in the
                        Hypnodyne ZMax software folder
  --zmax_ppgparser_timeout ZMAX_PPGPARSER_TIMEOUT
                        An optional timeout to run the ZMax PPGParser.exe in
                        seconds. If empty no timeout is used
  --zmax_lite           Switch to indicate if the device is a ZMax lite
                        version and not all channels have to be included
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
zmax_edf_merge_converter.exe "C:\my\zmax\files\are\in\subfolders\here" --zmax_lite --write_zip --read_zip
zmax_edf_merge_converter.exe "C:\my\zmax\files\are\in\subfolders\here" --zmax_ppgparser --zmax_ppgparser_exe_path="C:\Program Files (x86)\Hypnodyne\ZMax\PPGParser.exe"  --zmax_ppgparser_timeout=1000
zmax_edf_merge_converter.exe "C:\my\zmax\files\are\in\subfolders\here" --write_zip --exclude_empty_channels --zmax_ppgparser --zmax_ppgparser_exe_path="C:\Program Files (x86)\Hypnodyne\ZMax\PPGParser.exe"  --zmax_ppgparser_timeout=1000
zmax_edf_merge_converter.exe "C:\my\zmax\files\are\in\subfolders\here" --write_redirection_path="C:\and\shall\be\written\here\with\original\folder\structure" --write_zip --exclude_empty_channels --zmax_ppgparser --zmax_ppgparser_exe_path="C:\Program Files (x86)\Hypnodyne\ZMax\PPGParser.exe"  --zmax_ppgparser_timeout=1000

```