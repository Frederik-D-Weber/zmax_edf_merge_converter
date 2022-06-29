## zmax_edf_merge_converter
conversion of a folder with zmax EDF files (originally convered using Hypondyne HDRecorder.exe) into a merged European Data Format .EDF (EDF+)
- lets you open the EDF file also in other software (because there are often header issues with some channels in the converted .edf files from HDRecorder)
- without refiltering
- can read zipped zmax files
- can write zipped EDF files
- can reduce the channel set to the light/lite version of the zmax

### REQUIREMENTS:
python3.8

### TESTED ON:
Windows 7, x64

### INSTALLATION:
```
download the distribution zmax_edf_merge_converter.exe from the repository
```

### USAGE:
```
zmax_edf_merge_converter.exe [-h] [--zmax_light] [--read_zip]
                                    [--write_zip]
                                    parentdirpath

this is useful software to reuse EDF from zmax

positional arguments:
  parentdirpath  A path to the parent folder where the data is stored and to
                 be initialized

optional arguments:
  -h, --help     show this help message and exit
  --zmax_light   Switch to indicate if the device is a zmax light/lite version
                 and not all channels have to be included
  --read_zip     Switch to indicate if the input edfs are zipped and end with
                 .zip
  --write_zip    Switch to indicate if the output edfs should be zipped in one
                 .zip file
```
for example:
```
zmax_edf_merge_converter.exe "C:\my\zmax\files\are\in\subfolders\here"
zmax_edf_merge_converter.exe "C:\my\zmax\files\are\in\subfolders\here" --zmax_light --write_zip --read_zip
zmax_edf_merge_converter.exe "D:\FW" --zmax_light --write_zip --read_zip
```