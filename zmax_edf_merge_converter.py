# -*- coding: utf-8 -*-
"""
Copyright 2022, Frederik D. Weber

Notes:
conda create --name=hbs_wearables python=3
conda activate hbs_wearables

# install the requirements
pip install -r requirements.txt

# install them manually on the python version
# first make sure pip is up to date

python.exe -m pip install --upgrade pip
python.exe -m pip install -r requirements.txt


#or just do them step by step
python.exe -m pip install mne
python.exe -m pip install heartpy
python.exe -m pip install pyinstaller
...

or to save the enironment package requirements (also unused)
python.exe -m pip freeze > requirements.txt

or use project specific used packages:
pip install pipreqs
pipreqs /path/to/this/project


"""

import mne
import numpy
import warnings
import os
import glob
import datetime
import pyedflib
import shutil
import argparse
import pathlib

import sys
if sys.version_info >= (3, 6):
	import zipfile
	from zipfile import ZipFile
else:
	import zipfile36 as zipfile

import tempfile

# functions #

# =============================================================================
#
# =============================================================================
def fileparts(filepath):
	filepath = os.path.normpath(filepath)
	path_filename = os.path.split(filepath)
	filename = path_filename[1]
	path = path_filename[0]
	name_extension = os.path.splitext(filename)
	name = name_extension[0]
	extension = name_extension[1]
	return path, name, extension

# =============================================================================
#
# =============================================================================
def zip_directory(folderpath, zippath, deletefolder=False, compresslevel=6):
	with zipfile.ZipFile(zippath, mode='w') as zf:
		len_dir_path = len(folderpath)
		for root, _, files in os.walk(folderpath):
			for file in files:
				filepath = os.path.join(root, file)
				zf.write(filepath, filepath[len_dir_path:], compress_type=zipfile.ZIP_DEFLATED, compresslevel=compresslevel)
	if not deletefolder:
		shutil.rmtree(folderpath)

# =============================================================================
#
# =============================================================================
def safe_zip_dir_extract(filepath):
	temp_dir = tempfile.TemporaryDirectory()
	#temp_dir = tempfile.mkdtemp()
	with zipfile.ZipFile(filepath, 'r') as zipObj:
		zipObj.extractall(path=temp_dir.name)
	#temp_dir.cleanup()
	return temp_dir

# =============================================================================
#
# =============================================================================
def safe_zip_dir_cleanup(temp_dir):
	temp_dir.cleanup()

# =============================================================================
#
# =============================================================================
def read_edf_to_raw(filepath, preload=True, format="zmax_edf", drop_zmax = ['BODY TEMP', 'LIGHT', 'NASAL L', 'NASAL R', 'NOISE', 'OXY_DARK_AC', 'OXY_DARK_DC', 'OXY_R_AC', 'OXY_R_DC', 'RSSI']):
	path, name, extension = fileparts(filepath)
	if (extension).lower() != ".edf":
		warnings.warn("The filepath " + filepath + " does not seem to be an EDF file.")
	raw = None
	if format == "zmax_edf":

		"""
		This reader is largely similar to the one for edf but gets and assembles all the EDFs in a folder if they are in the zmax data format
		"""
		path, name, extension = fileparts(filepath)
		check_channel_filenames = ['BATT', 'BODY TEMP', 'dX', 'dY', 'dZ', 'EEG L', 'EEG R', 'LIGHT', 'NASAL L', 'NASAL R', 'NOISE', 'OXY_DARK_AC', 'OXY_DARK_DC', 'OXY_IR_AC', 'OXY_IR_DC', 'OXY_R_AC', 'OXY_R_DC', 'RSSI']
		raw_avail_list = []
		channel_avail_list = []
		channel_read_list = []
		for iCh, name in enumerate(check_channel_filenames):
			checkname = path + os.sep + name + '.edf'
			if os.path.isfile(checkname):
				channel_avail_list.append(check_channel_filenames[iCh])
				if not name in drop_zmax:
					raw_avail_list.append(read_edf_to_raw(checkname, format="edf"))
					channel_read_list.append(check_channel_filenames[iCh])
		print("zmax edf channels found:")
		print(channel_avail_list)
		print("zmax edf channels read in:")
		print(channel_read_list)

		# append the raws together
		raw = raw_avail_list[0].add_channels(raw_avail_list[1:])

		# also append the units as this is not handled by raw.add_channels
		raw._raw_extras[0]['cal'] = [].append(raw._raw_extras[0]['cal'])
		for r in raw_avail_list[1:]:
			raw._orig_units.update(r._orig_units)
			ch_name = r._raw_extras[0]['ch_names'][0]
			raw._raw_extras[0]['cal'] = numpy.append(raw._raw_extras[0]['cal'],r._raw_extras[0]['cal'])
			raw._raw_extras[0]['ch_names'].append(r._raw_extras[0]['ch_names'])
			raw._raw_extras[0]['ch_types'].append(r._raw_extras[0]['ch_types'])
			if ch_name in ['EEG L', 'EEG R']:
				raw._raw_extras[0]['digital_max'] = numpy.append(raw._raw_extras[0]['digital_max'],32767)
				raw._raw_extras[0]['physical_max'] = numpy.append(raw._raw_extras[0]['physical_max'],1976)
				try: # as in nme this is deleted while reading in
					raw._raw_extras[0]['digital_min'] = numpy.append(raw._raw_extras[0]['digital_min'],-32767)
					raw._raw_extras[0]['physical_min'] = numpy.append(raw._raw_extras[0]['physical_min'],-1976)
				except:
					pass
			else:
				raw._raw_extras[0]['digital_max'] = numpy.append(raw._raw_extras[0]['digital_max'],r._raw_extras[0]['digital_max'])
				raw._raw_extras[0]['physical_max'] = numpy.append(raw._raw_extras[0]['physical_max'],r._raw_extras[0]['physical_max'])
				try: # as in nme this is deleted while reading in
					raw._raw_extras[0]['digital_min'] = numpy.append(raw._raw_extras[0]['digital_min'],r._raw_extras[0]['digital_min'])
					raw._raw_extras[0]['physical_min'] = numpy.append(raw._raw_extras[0]['physical_min'],r._raw_extras[0]['physical_min'])
				except:
					pass
			raw._raw_extras[0]['highpass'] = numpy.append(raw._raw_extras[0]['highpass'],r._raw_extras[0]['highpass'])
			raw._raw_extras[0]['lowpass'] = numpy.append(raw._raw_extras[0]['lowpass'],r._raw_extras[0]['lowpass'])
			raw._raw_extras[0]['n_samps'] = numpy.append(raw._raw_extras[0]['n_samps'],r._raw_extras[0]['n_samps'])
			raw._raw_extras[0]['offsets'] = numpy.append(raw._raw_extras[0]['offsets'],r._raw_extras[0]['offsets'])
			raw._raw_extras[0]['units'] = numpy.append(raw._raw_extras[0]['units'],r._raw_extras[0]['units'])

		raw._raw_extras[0]['sel'] = range(channel_avail_list.__len__())
		raw._raw_extras[0]['n_chan'] = channel_avail_list.__len__()
		raw._raw_extras[0]['orig_n_chan'] = channel_avail_list.__len__()

		#raw.info['chs'][0]['unit']
	else:
		raw = mne.io.read_raw_edf(filepath, preload = True)
	return raw

# =============================================================================
#
# =============================================================================
def edfWriteAnnotation(edfWriter, onset_in_seconds, duration_in_seconds, description, str_format='utf-8'):
	edfWriter.writeAnnotation(onset_in_seconds, duration_in_seconds, description, str_format)

# =============================================================================
#
# =============================================================================
def write_raw_to_edf(raw, filepath, format="zmax_edf"):
	path, name, extension = fileparts(filepath)
	if (extension).lower() != ".edf":
		warnings.warn("The filepath " + filepath + " does not seem to be an EDF file.")
	if format == "zmax_edf":
		channel_dimensions_zmax = {'BATT': 'V', 'BODY TEMP': "C", 'dX': "g", 'dY': "g", 'dZ': "g", 'EEG L': "uV", 'EEG R': "uV", 'LIGHT': "", 'NASAL L': "", 'NASAL R': "", 'NOISE': "", 'OXY_DARK_AC': "", 'OXY_DARK_DC': "", 'OXY_IR_AC': "", 'OXY_IR_DC': "", 'OXY_R_AC': "", 'OXY_R_DC': "", 'RSSI': ""}

		#EDF_format_extention = ".edf"
		EDF_format_filetype = pyedflib.FILETYPE_EDFPLUS
		#temp_filterStringHeader = 'HP ' + str(self.prefilterEDF_hp) + ' Hz'
		nAnnotation = 1
		has_annotations = False
		nChannels = raw.info['nchan']
		sfreq = raw.info['sfreq']
		edfWriter = pyedflib.EdfWriter(filepath, nChannels, file_type=EDF_format_filetype)

		"""
		Only when the number of annotations you want to write is more than the number of seconds of the duration of the recording, you can use this function to increase the storage space for annotations */
		/* Minimum is 1, maximum is 64 */
		"""
		if has_annotations:
			edfWriter.set_number_of_annotation_signals(nAnnotation) #nAnnotation*60 annotations per minute on average
		edfWriter.setTechnician('')
		edfWriter.setRecordingAdditional('merged from single zmax files')
		edfWriter.setPatientName('')
		edfWriter.setPatientCode('')
		edfWriter.setPatientAdditional('')
		edfWriter.setAdmincode('')
		edfWriter.setEquipment('Hypnodyne zmax')
		edfWriter.setGender(0)
		edfWriter.setBirthdate(datetime.date(2000, 1, 1))
		#edfWriter.setStartdatetime(datetime.datetime.now())
		edfWriter.setStartdatetime(raw.info['meas_date'])
		edfWriteAnnotation(edfWriter,0, -1, u"signal_start")

		for iCh in range(0,nChannels):
			ch_name = raw.info['ch_names'][iCh]
			dimension = channel_dimensions_zmax[ch_name] #'uV'
			sf = int(round(sfreq))
			pysical_min = raw._raw_extras[0]['physical_min'][iCh]
			pysical_max = raw._raw_extras[0]['physical_max'][iCh]
			digital_min = raw._raw_extras[0]['digital_min'][iCh]
			digital_max = raw._raw_extras[0]['digital_max'][iCh]
			prefilter = 'HP:0.1Hz LP:75Hz'

			channel_info = {'label': ch_name, 'dimension': dimension, 'sample_rate': sf,
							'physical_max': pysical_max, 'physical_min': pysical_min,
							'digital_max': digital_max, 'digital_min': digital_min,
							'prefilter': prefilter, 'transducer': 'none'}

			edfWriter.setSignalHeader(iCh, channel_info)
			edfWriter.setLabel(iCh, ch_name)

		data = raw.get_data()
		data_list = []
		for iCh in range(0,nChannels):
			data_list.append(data[iCh,] / raw._raw_extras[0]['units'][iCh])
		edfWriter.writeSamples(data_list, digital = False) # write physical samples

		#for iChannel_all in range(0, nChannels):
		#	edfWriter.writePhysicalSamples(data[iChannel_all,])

		edfWriter.close()
	else:
		raw.export(filepath,fmt='edf', physical_range='auto', add_ch_type=False, overwrite=True, verbose=None)
	return filepath

# =============================================================================
#
# =============================================================================
def read_edf_to_raw_zipped(filepath, format="zmax_edf", drop_zmax=['BODY TEMP', 'LIGHT', 'NASAL L', 'NASAL R', 'NOISE', 'OXY_DARK_AC', 'OXY_DARK_DC', 'OXY_R_AC', 'OXY_R_DC', 'RSSI']):
	temp_dir = safe_zip_dir_extract(filepath)
	raw = None
	if format == "zmax_edf":
		raw = read_edf_to_raw(temp_dir.name + os.sep + "EEG L.edf", format=format, drop_zmax=drop_zmax)
	elif format == "edf":
		fileendings = ('*.edf', '*.EDF')
		filepath_list_edfs = []
		for fileending in fileendings:
			filepath_list_edfs.extend(glob.glob(temp_dir.name + os.sep + fileending,recursive=True))
		if filepath_list_edfs:
			raw = read_edf_to_raw(filepath_list_edfs[0], format=format)
	safe_zip_dir_cleanup(temp_dir)
	return raw

# =============================================================================
#
# =============================================================================
def write_raw_to_edf_zipped(raw, zippath, format="zmax_edf", compresslevel=6):
	temp_dir = tempfile.TemporaryDirectory()
	filepath = temp_dir.name + os.sep + fileparts(zippath)[1] + '.edf'
	write_raw_to_edf(raw, filepath, format)
	zip_directory(temp_dir.name, zippath, deletefolder=True, compresslevel=compresslevel)
	safe_zip_dir_cleanup(temp_dir)
	return zippath


def nullable_string(val):
	if not val:
		return None
	return val

def dir_path(pathstring):
	pathstring = os.path.normpath(pathstring)
	if nullable_string(pathstring):
		if os.path.isdir(pathstring):
			return pathstring
		else:
			print("'%s' is not a directory" % pathstring)
			raise NotADirectoryError(pathstring)
	return None

# =============================================================================
# 
# =============================================================================
def find_zmax_files(parentdirpath,readzip=False):
	"""
	finds all the zmax data from different wearables in the HB file structure given the parent path to the subject files
	:param wearable:
	:return:
	"""
	filepath_list = []
	wearable = 'zmx'
	if readzip:
		filepath_list = glob.glob(parentdirpath + os.sep + "**" + os.sep + "*.zip",recursive=True)
	else:
		filepath_list = glob.glob(parentdirpath + os.sep + "**" + os.sep + "EEG L.edf",recursive=True)

	# # compatible with python versions < 3.10 remove the root_dir
	# for i, filepath in enumerate(filepath_list):
	# 	filepath_list[i] = filepath.replace(parentdirpath + os.sep,"")

	return filepath_list


if __name__ == "__main__":
# Instantiate the argument parser
	parser = argparse.ArgumentParser(prog='zmax_edf_merge_converter.exe', description='this is useful software to reuse EDF from zmax')

	# Required positional argument
	parser.add_argument('parentdirpath', type=dir_path,
					help='A path to the parent folder where the data is stored and to be initialized')

	# Switch
	parser.add_argument('--zmax_light', action='store_true',
					help='Switch to indicate if the device is a zmax light/lite version and not all channels have to be included')

	# Switch
	parser.add_argument('--read_zip', action='store_true',
					help='Switch to indicate if the input edfs are zipped and end with .zip')

	# Switch
	parser.add_argument('--write_zip', action='store_true',
					help='Switch to indicate if the output edfs should be zipped in one .zip file')



	args = parser.parse_args()

	parentdirpath = pathlib.Path().resolve() # the current working directory
	if args.parentdirpath is not None:
		parentdirpath = args.parentdirpath

	islightversion = False
	if args.zmax_light is not None:
		islightversion = args.zmax_light
	
	write_zip = False
	if args.write_zip is not None:
		write_zip = args.write_zip

	read_zip = False
	if args.read_zip is not None:
		read_zip = args.read_zip


	#if len(sys.argv) != 3:
	#	print('expecting path to a parent folders with zmax edfs converted from HDrecorder as the only argument')
	#	exit(0)

	#parentdirpath = sys.argv[1]

	try:
		parentdirpath = dir_path(parentdirpath)
	except NotADirectoryError:
		print("argument '%s' is not a directory" %parentdirpath)
		exit(0)
	
	if parentdirpath is None:
		print("argument '%s' is not parsable" %parentdirpath)
		exit(0)
	
	filepath_list = find_zmax_files(parentdirpath, readzip=read_zip)
	
	if len(filepath_list) < 1:
		print("no zmax edf files found")
		exit(0)

	number_of_conversions = len(filepath_list)
	for i, filepath in enumerate(filepath_list):
		print("PROCESSING %d of %d: '%s' " % (i+1, number_of_conversions, filepath))
		path, name, extension = fileparts(filepath)
		parentfoldername = os.path.basename(path)
		pathup, nametmp, extensiontmp = fileparts(path)
		drop_channels = []
		if islightversion:
			drop_channels = ['BODY TEMP', 'LIGHT', 'NASAL L', 'NASAL R', 'NOISE', 'OXY_DARK_AC', 'OXY_DARK_DC', 'OXY_R_AC', 'OXY_R_DC', 'RSSI']
		try:
			if read_zip:
				raw = read_edf_to_raw_zipped(filepath, format="zmax_edf", drop_zmax=drop_channels)
				export_filepath = path + os.sep + name + "_merged"
			else:
				raw = read_edf_to_raw(filepath, format="zmax_edf", drop_zmax = drop_channels)
				export_filepath = pathup + os.sep +  parentfoldername + "_merged"
			print("READ %d of %d: '%s' " % (i+1, number_of_conversions, filepath))

			if write_zip:
				export_filepath_final = write_raw_to_edf_zipped(raw, export_filepath + ".zip", format="zmax_edf") # treat as a speacial zmax read EDF for export
			else:
				export_filepath_final = write_raw_to_edf(raw, export_filepath + ".edf", format="zmax_edf")  # treat as a speacial zmax read EDF for export
			print("WROTE %d of %d: '%s' " % (i+1, number_of_conversions, export_filepath_final))

		except:
			print("FAILED %d of %d: '%s' " % (i+1, number_of_conversions, filepath))
