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
import traceback
import subprocess
import logging
import statistics
import hashlib
import csv
import pandas

# classes #

class StreamToLogger(object):
	def __init__(self, logger, log_level=logging.INFO):
		self.logger = logger
		self.log_level = log_level
		self.linebuf = ''

	def write(self, buf):
		for line in buf.rstrip().splitlines():
			self.logger.log(self.log_level, line.rstrip())

# functions #


# =============================================================================
# hashlib.md5 is slower than hashlib.blake2b
# =============================================================================
def get_file_hash(filepath, chunk_size_bytes=None, start_chunk=None, stop_chunk=None, hash_function=hashlib.md5):
	with open(filepath, "rb") as f:
		if chunk_size_bytes is None:
			return hash_function(f.read()).hexdigest()
		else:
			file_hash = hash_function()
			chunk = f.read(chunk_size_bytes)
			iChunk = 1
			while chunk:
				if start_chunk is None:
					if stop_chunk is None:
						file_hash.update(chunk)
					else:
						if stop_chunk <= iChunk:
							file_hash.update(chunk)
				else:
					if start_chunk >= iChunk:
						if stop_chunk <= iChunk:
							file_hash.update(chunk)
				chunk = f.read(chunk_size_bytes)
				iChunk += 1
			return file_hash.hexdigest()

# =============================================================================
# hashlib.md5 is slower than hashlib.blake2b
# =============================================================================
def get_raw_data_hash(raw, hash_function=hashlib.md5):
		return hash_function(raw._data.tobytes()).hexdigest()

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
def zip_file(filepath, zippath, deletefile=False, compresslevel=6):
	with zipfile.ZipFile(zippath, mode='w') as zf:
		len_dir_path = len(fileparts(filepath)[0])
		zf.write(filepath, filepath[len_dir_path:], compress_type=zipfile.ZIP_DEFLATED, compresslevel=compresslevel)
	if deletefile:
		os.remove(filepath)
	return zippath
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
	if deletefolder:
		shutil.rmtree(folderpath)
	return zippath

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
def raw_prolong_constant(raw, to_n_samples, contant=0, prepend=False):
	append_samples = to_n_samples - raw.n_times

	#raw_append = mne.io.RawEDF(numpy.full([raw._data.shape[0], append_samples], contant), info=raw.info)
	raw_append = raw.copy()
	raw_append.crop(tmin=raw_append.times[0], tmax=raw_append.times[append_samples-1], include_tmax=True, verbose=False)
	raw_append._data = numpy.full([raw_append._data.shape[0], append_samples], contant)
	if prepend:
		raw_append.append([raw])
		return raw_append
	else:
		raw.append([raw_append])
		return raw
		#mne.concatenate_raws([raw, raw_append])

def get_check_channel_filenames():
	return ['BATT', 'BODY TEMP', 'dX', 'dY', 'dZ', 'EEG L', 'EEG R', 'EEG R Cleaned', 'EEG L Cleaned', 'EEG R Cleaned_LFP', 'EEG L Cleaned_LFP', 'LIGHT', 'NASAL L', 'NASAL R', 'NOISE', 'OXY_DARK_AC', 'OXY_DARK_DC', 'OXY_IR_AC', 'OXY_IR_DC', 'OXY_R_AC', 'OXY_R_DC', 'RSSI', 'PARSED_NASAL R', 'PARSED_OXY_IR_AC', 'PARSED_NASAL L', 'PARSED_HR_r', 'PARSED_HR_r_strength', 'PARSED_OXY_R_AC', 'PARSED_HR_ir', 'PARSED_HR_ir_strength']

# =============================================================================
#
# =============================================================================
def read_edf_to_raw(filepath, preload=True, format="zmax_edf", zmax_ppgparser=False, zmax_ppgparser_exe_path=None, zmax_ppgparser_timeout_seconds=None, zmax_eegcleaner=False, zmax_eegcleaner_exe_path=None, zmax_eegcleaner_timeout_seconds=None, zmax_edfjoin_exe_path=None, zmax_edfjoin_timeout_seconds=None, zmax_edfjoin_keep=False, zmax_edfjoin_move_path=None, no_read=False, drop_zmax=['BODY TEMP', 'LIGHT', 'NASAL L', 'NASAL R', 'NOISE', 'OXY_DARK_AC', 'OXY_DARK_DC', 'OXY_R_AC', 'OXY_R_DC', 'RSSI', 'PARSED_NASAL R', 'PARSED_NASAL L', 'PARSED_OXY_R_AC', 'PARSED_HR_r', 'PARSED_HR_r_strength']):
	path, name, extension = fileparts(filepath)
	if (extension).lower() != ".edf":
		warnings.warn("The filepath " + filepath + " does not seem to be an EDF file.")
	raw = None
	if format in ["zmax_edf", "zmax_edf_join"]:

		"""
		This reader is largely similar to the one for edf but gets and assembles all the EDFs in a folder if they are in the zmax data format
		"""
		path, name, extension = fileparts(filepath)
		check_channel_filenames = get_check_channel_filenames()
		raw_avail_list = []
		channel_avail_list = []
		channel_read_list = []
		for iCh, name in enumerate(check_channel_filenames):
			checkname = path + os.sep + name + '.edf'
			if os.path.isfile(checkname):
				channel_avail_list.append(name)

		reprocessed = False
		if zmax_ppgparser and zmax_ppgparser_exe_path is not None:
			print('ATTEMPT to reparse heart signals using the PPGParser ' + filepath)
			exec_string =  "\"" + zmax_ppgparser_exe_path + "\""
			for iCh, name in enumerate(channel_avail_list):
				addfilepath = path + os.sep + name + '.edf'
				exec_string = exec_string + " " + "\"" + addfilepath + "\""
			try:
				reprocessed = True
				subprocess.run(exec_string, shell=False, timeout=zmax_ppgparser_timeout_seconds)
			except:
				print(traceback.format_exc())
				print('FAILED to reparse ' + filepath)


		if zmax_eegcleaner and zmax_eegcleaner_exe_path is not None:
			print('ATTEMPT to clean the EEG signals using the EDFCleaner ' + filepath)
			exec_string =  "\"" + zmax_eegcleaner_exe_path + "\""
			hasEEG = False
			for iCh, name in enumerate(channel_avail_list):
				if name in ['EEG L', 'EEG R']:
					hasEEG = True
					addfilepath = path + os.sep + name + '.edf'
					exec_string = exec_string + " " + "\"" + addfilepath + "\""
			try:
				if hasEEG:
					reprocessed = True
					subprocess.run(exec_string, shell=False, timeout=zmax_eegcleaner_timeout_seconds)
			except:
				print(traceback.format_exc())
				print('FAILED to clean EEG from ' + filepath)

		if reprocessed:
			channel_avail_list = []
			for iCh, name in enumerate(check_channel_filenames):
				checkname = path + os.sep + name + '.edf'
				if os.path.isfile(checkname):
					channel_avail_list.append(name)

		if format == "zmax_edf_join":
			joined_filepath = None
			if channel_avail_list:
				print('ATTEMPT to join the EDF signals using the EDFJoin ' + filepath)
				hasChannel = False
				exec_string =  "\"" + zmax_edfjoin_exe_path + "\""
				for iCh, name in enumerate(channel_avail_list):
					if not name in drop_zmax:
						hasChannel = True
						addfilepath = path + os.sep + name + '.edf'
						exec_string = exec_string + " " + "\"" + addfilepath + "\""
				try:
					if hasChannel:
						subprocess.run(exec_string, shell=False, timeout=zmax_edfjoin_timeout_seconds)
						#joined_filepath = path + os.sep + 'out.EDF'
						joined_filepath = os.path.abspath(os.getcwd()) + os.sep + 'out.EDF'
						if not no_read:
							raw = mne.io.read_raw_edf(joined_filepath, preload=preload)
						if zmax_edfjoin_move_path != None:
							try:
								joined_filepath_moved = shutil.move(joined_filepath, zmax_edfjoin_move_path)
								zmax_edfjoin_keep = False
								joined_filepath = joined_filepath_moved
							except Exception:
								print('FAILED TO MOVE THE file %s to %s' % (joined_filepath, zmax_edfjoin_move_path))
								print(traceback.format_exc())
							if no_read:
								return joined_filepath
						if not zmax_edfjoin_keep:
							if os.path.exists(joined_filepath):
								try:
									os.remove(joined_filepath)
								except FileNotFoundError:
									pass
				except:
					print(traceback.format_exc())
					print('FAILED to join ZMax EDF files from ' + filepath)

		elif format == "zmax_edf":
			for iCh, name in enumerate(channel_avail_list):
				if not name in drop_zmax:
					readfilepath = path + os.sep + name + '.edf'
					try:
						raw_read = read_edf_to_raw(readfilepath, format="edf")
						if 'PARSED_' in name:
							raw_read.rename_channels({raw_read.info["ch_names"][0]: name})
						raw_avail_list.append(raw_read)
						channel_read_list.append(name)
					except Exception:
						print(traceback.format_exc())
						print('FAILED TO read in channel: ' + check_channel_filenames[iCh])

			print("zmax edf channels found:")
			print(channel_avail_list)
			print("zmax edf channels read in:")
			print(channel_read_list)

			if raw_avail_list[0] is not None:
				nSamples_should = raw_avail_list[0].n_times

			for i, r in enumerate(raw_avail_list):
				if r is not None:
					sfreq_temp = r.info['sfreq']
					if sfreq_temp != 256.0:
						raw_avail_list[i] = r.resample(256.0)
						nSamples = raw_avail_list[i].n_times
						if nSamples < nSamples_should:
							raw_avail_list[i] = raw_prolong_constant(raw_avail_list[i], nSamples_should, contant=0, prepend=True)

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
				if ch_name in ['EEG L', 'EEG R', 'EEG R Cleaned', 'EEG L Cleaned', 'EEG R Cleaned_LFP', 'EEG L Cleaned_LFP']:
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
		raw = mne.io.read_raw_edf(filepath, preload=preload)
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
		channel_dimensions_zmax = {'BATT': 'V', 'BODY TEMP': "C", 'dX': "g", 'dY': "g", 'dZ': "g", 'EEG L': "uV", 'EEG R': "uV", 'EEG R Cleaned': "uV", 'EEG L Cleaned': "uV", 'EEG R Cleaned_LFP': "uV", 'EEG L Cleaned_LFP': "uV", 'LIGHT': "", 'NASAL L': "", 'NASAL R': "", 'NOISE': "", 'OXY_DARK_AC': "", 'OXY_DARK_DC': "", 'OXY_IR_AC': "", 'OXY_IR_DC': "", 'OXY_R_AC': "", 'OXY_R_DC': "", 'RSSI': "", 'PARSED_NASAL R': "", 'PARSED_OXY_IR_AC': "", 'PARSED_NASAL L': "", 'PARSED_HR_r': "bpm", 'PARSED_HR_r_strength': "", 'PARSED_OXY_R_AC': "", 'PARSED_HR_ir': "bpm", 'PARSED_HR_ir_strength': ""}

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
			try:
				dimension = channel_dimensions_zmax[ch_name] #'uV'
			except KeyError:
				dimension = ""
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
def read_edf_to_raw_zipped(filepath, format="zmax_edf", zmax_ppgparser=False, zmax_ppgparser_exe_path=None, zmax_ppgparser_timeout_seconds=None, zmax_eegcleaner=False, zmax_eegcleaner_exe_path=None, zmax_eegcleaner_timeout_seconds=None, zmax_edfjoin_exe_path=None, zmax_edfjoin_timeout_seconds=None, zmax_edfjoin_keep=False, zmax_edfjoin_move_path=None, no_read=False, drop_zmax=['BODY TEMP', 'LIGHT', 'NASAL L', 'NASAL R', 'NOISE', 'OXY_DARK_AC', 'OXY_DARK_DC', 'OXY_R_AC', 'OXY_R_DC', 'RSSI', 'PARSED_NASAL R', 'PARSED_NASAL L', 'PARSED_OXY_R_AC', 'PARSED_HR_r', 'PARSED_HR_r_strength']):
	temp_dir = safe_zip_dir_extract(filepath)
	raw = None
	if format in ["zmax_edf", "zmax_edf_join"]:
		raw = read_edf_to_raw(temp_dir.name + os.sep + "EEG L.edf", format=format, zmax_ppgparser=zmax_ppgparser, zmax_ppgparser_exe_path=zmax_ppgparser_exe_path, zmax_ppgparser_timeout_seconds=zmax_ppgparser_timeout_seconds, zmax_eegcleaner=zmax_eegcleaner, zmax_eegcleaner_exe_path=zmax_eegcleaner_exe_path, zmax_eegcleaner_timeout_seconds=zmax_eegcleaner_timeout_seconds, zmax_edfjoin_exe_path=zmax_edfjoin_exe_path, zmax_edfjoin_timeout_seconds=zmax_edfjoin_timeout_seconds, zmax_edfjoin_keep=zmax_edfjoin_keep, zmax_edfjoin_move_path=zmax_edfjoin_move_path, no_read=no_read, drop_zmax=drop_zmax)
	elif format == "edf":
		fileendings = ('*.edf', '*.EDF')
		filepath_list_edfs = []
		for fileending in fileendings:
			filepath_list_edfs.extend(glob.glob(temp_dir.name + os.sep + fileending,recursive=True))
		if filepath_list_edfs:
			raw = read_edf_to_raw(filepath_list_edfs[0], format=format, zmax_ppgparser=zmax_ppgparser, zmax_ppgparser_exe_path=zmax_ppgparser_exe_path, zmax_ppgparser_timeout_seconds=zmax_ppgparser_timeout_seconds, zmax_eegcleaner=zmax_eegcleaner, zmax_eegcleaner_exe_path=zmax_eegcleaner_exe_path, zmax_eegcleaner_timeout_seconds=zmax_eegcleaner_timeout_seconds, zmax_edfjoin_exe_path=None, zmax_edfjoin_timeout_seconds=None, no_read=no_read)
	safe_zip_dir_cleanup(temp_dir)
	return raw

# =============================================================================
#
# =============================================================================
def write_raw_to_edf_zipped(raw, zippath, edf_filename=None, format="zmax_edf", compresslevel=6):
	temp_dir = tempfile.TemporaryDirectory()
	if edf_filename is None:
		filepath = temp_dir.name + os.sep + fileparts(zippath)[1] + '.edf'
	else:
		filepath = temp_dir.name + os.sep + fileparts(edf_filename)[1] + '.edf'
	write_raw_to_edf(raw, filepath, format)
	zip_directory(temp_dir.name, zippath, deletefolder=False, compresslevel=compresslevel)
	safe_zip_dir_cleanup(temp_dir)
	return zippath

# =============================================================================
#
# =============================================================================
def raw_zmax_data_quality(raw):
		# the last second of Battery voltage
		quality = None
		try:
			quality = statistics.mean(raw.get_data(picks=['BATT'])[0][-256:])
		except Exception:
			print(traceback.format_exc())
		return quality

def get_dir_path(pathstring):
	pathstring = os.path.normpath(pathstring)
	if os.path.isdir(pathstring):
		return pathstring
	elif os.path.isfile(pathstring):
		p, n, e = fileparts(pathstring)
		return p + os.sep + n
	else:
		p, n, e = fileparts(pathstring)
		if e:
			return p + os.sep + n
		else:
			return pathstring
		print("'%s' is not a file or directory" % pathstring)
		raise Exception(pathstring)
	return None

def nullable_string(val):
	if not val:
		return None
	return val

def dir_path_or_file(pathstring):
	pathstring = os.path.normpath(pathstring)
	if nullable_string(pathstring):
		if os.path.isdir(pathstring):
			return pathstring
		if os.path.isfile(pathstring):
			return pathstring
		else:
			print("'%s' is not a directory or file" % pathstring)
			raise NotADirectoryError(pathstring)
	return None

def dir_path(pathstring):
	pathstring = os.path.normpath(pathstring)
	if nullable_string(pathstring):
		if os.path.isdir(pathstring):
			return pathstring
		else:
			print("'%s' is not a directory" % pathstring)
			raise NotADirectoryError(pathstring)
	return None

def dir_path_new(pathstring):
	pathstring = os.path.normpath(pathstring)
	if nullable_string(pathstring):
		return pathstring
	return None

def file_path(pathstring):
	pathstring = os.path.normpath(pathstring)
	if nullable_string(pathstring):
		if os.path.isfile(pathstring):
			return pathstring
		else:
			print("'%s' is not a file" % pathstring)
			raise NotADirectoryError(pathstring)
	return None

def dir_path_create(pathstring):
	if nullable_string(pathstring):
		try:
			pathstring = dir_path(pathstring)
			return pathstring
		except NotADirectoryError:
			try:
				os.makedirs(pathstring, exist_ok=True)
				print("Directory '%s' was not existent and was created" %pathstring)
			except:
				print("Directory '%s' was could not be created" %pathstring)
				NotADirectoryError(pathstring)
			finally:
				return nullable_string(pathstring)
	else:
		return None

# =============================================================================
# 
# =============================================================================
def find_zmax_files(parentdirpath, readzip=False, zipfile_match_string='', zipfile_nonmatch_string='', find_hyp_files=False):
	"""
	finds all the zmax data from different wearables in the HB file structure given the parent path to the subject files
	:param wearable:
	:return:
	"""
	filepath_list = []
	if readzip:
		filepath_list = glob.glob(parentdirpath + os.sep + "**" + os.sep + "*.zip",recursive=True)

		if zipfile_match_string != '' or  (zipfile_match_string is None):
			for include_string in zipfile_match_string.split('|'):
				filepath_list = list(filter(lambda x: (include_string in fileparts(x)[1]), filepath_list))

		if zipfile_nonmatch_string != '' or  (zipfile_nonmatch_string is None):
			for exclude_string in zipfile_nonmatch_string.split('|'):
				filepath_list = list(filter(lambda x: (exclude_string not in fileparts(x)[1]), filepath_list))
	else:
		if find_hyp_files:
			filepath_list = glob.glob(parentdirpath + os.sep + "**" + os.sep + "*.hyp",recursive=True)
		else:
			filepath_list = glob.glob(parentdirpath + os.sep + "**" + os.sep + "EEG L.edf",recursive=True)

	# # compatible with python versions < 3.10 remove the root_dir
	# for i, filepath in enumerate(filepath_list):
	# 	filepath_list[i] = filepath.replace(parentdirpath + os.sep,"")

	return filepath_list

def path_create(path, isFile=False):
	if isFile:
		path, name, extension = fileparts(path)
	if not os.path.exists(path):
		os.makedirs(path)

if __name__ == "__main__":

	# determine if application is a script file or frozen exe
	application_path = ''
	if getattr(sys, 'frozen', False):
		application_path = os.path.dirname(sys.executable)
	elif __file__:
		application_path = os.path.dirname(__file__)

	# Instantiate the argument parser
	parser = argparse.ArgumentParser(prog='zmax_edf_merge_converter.exe', description='This is useful software to reuse EDF from zmax to repackage the original exported EDFs and reparse them if necessary or zip them. Copyright 2022, Frederik D. Weber')

	# Required positional argument
	parser.add_argument('parent_dir_paths', type=dir_path_or_file,
					help='A path or multiple paths to the parent folder where the data is stored and converted from (and by default also converted to)', nargs='+')

	# Optional argument
	parser.add_argument('--write_redirection_path', type=dir_path_new,
					help='An optional path to redirect writing to a different parent folder (so to not accidentally overwrite other files). Original folder structure is keept in the subfolders.')

	# Switch
	parser.add_argument('--read_zip', action='store_true',
					help='Switch to indicate if the input edfs are zipped and end with .zip')

	# Optional argument
	parser.add_argument('--zipfile_match_string', type=str,
					help='An optional string to match the name of the zip files to search for. Use the pipe to separate different search/match strings, e.g. --zipfile_match_string=\"this|that\" will search for \"this\" and then for \"that\". If parent_dir_paths contains direct paths to .zip files this does not apply.')

	# Optional argument
	parser.add_argument('--zipfile_nonmatch_string', type=str,
					help='An optional string to NOT match (i.e. exclude or filter out) after all the zipfile_match_string zip files have been found. Use the pipe to separate different search/match strings, e.g. --zipfile_nonmatch_string=\"this|that\" will search for \"this\" and then for \"that\". If parent_dir_paths contains direct paths to .zip files this does not apply.')

	# Switch
	parser.add_argument('--zmax_ppgparser', action='store_true',
					help='Switch to indicate if ZMax PPGParser.exe is used to reparse some heart rate related channels. you also need to specify zmax_ppgparser_exe_path if it is not already in the current directory. This will take time to reprocess each data.')

	# Optional argument
	parser.add_argument('--zmax_ppgparser_exe_path', type=file_path,
					help='direct and full path to the ZMax PPGParser.exe in the Hypnodyne ZMax software folder')

	# Optional argument
	parser.add_argument('--zmax_ppgparser_timeout_seconds', type=float,
					help='An optional timeout to run the ZMax PPGParser.exe in seconds. If empty no timeout is used')

	# Switch
	parser.add_argument('--zmax_edfjoin', action='store_true',
					help='Switch to indicate if ZMax EDFJoin.exe is used to merge the converted ZMax EDF files. you also need to specify zmax_edfjoin_exe_path if it is not already in the current directory. This will take time to reprocess each data. Note that this will disable resampling or cleaning of empty channels or some skip some values in an entry of the summary csv')

	# Optional argument
	parser.add_argument('--zmax_edfjoin_exe_path', type=file_path,
					help='direct and full path to the ZMax EDFJoin.exe in the Hypnodyne ZMax software folder')

	# Optional argument
	parser.add_argument('--zmax_edfjoin_timeout_seconds', type=float,
					help='An optional timeout to run the ZMax EDFJoin.exe in seconds. If empty no timeout is used')

	# Switch
	parser.add_argument('--zmax_eegcleaner', action='store_true',
					help='Switch to indicate if ZMax EDFCleaner.exe is used to clean the EEG channels from SD-card writing noise in 85.33 Hz and higher and lower harmonics (e.g. 42.66, 21.33, 10.66, 5.33 Hz...) you also need to specify zmax_eegcleaner_exe_path if it is not already in the current directory. This will take time to reprocess each data.')

	# Optional argument
	parser.add_argument('--zmax_eegcleaner_exe_path', type=file_path,
					help='direct and full path to the ZMax EDFCleaner.exe in the Hypnodyne ZMax software folder')

	# Optional argument
	parser.add_argument('--zmax_eegcleaner_timeout_seconds', type=float,
					help='An optional timeout to run the ZMax EDFCleaner.exe in seconds. If empty no timeout is used')

	# Switch
	parser.add_argument('--zmax_raw_hyp_file', action='store_true',
					help='Switch to indicate if ZMax HDRecorder.exe is used to convert from .hyp files moved from the SD card. you need to specify zmax_hdrecorder_exe_path if it is not already in the current directory. This will take time to reprocess each data.')

	# Optional argument
	parser.add_argument('--zmax_hdrecorder_exe_path', type=file_path,
					help='direct and full path to the ZMax HDRecorder.exe in the Hypnodyne ZMax software folder')

	# Optional argument
	parser.add_argument('--zmax_hdrecorder_timeout_seconds', type=float,
					help='An optional timeout to run the ZMax HDRecorder.exe in seconds. If empty no timeout is used')

	# Switch
	parser.add_argument('--zmax_raw_hyp_keep_edf', action='store_true',
					help='Switch to indicate if after conversion with ZMax HDRecorder.exe from .hyp files also the converted .edf files in the subfolders should be kept. Note, this wont apply for zipped .hyp files.')

	# Optional argument
	parser.add_argument('--write_name_postfix', type=str,
					help='file name post fix for the written files or directories. Default is \"_merged\"')

	# Optional argument
	parser.add_argument('--temp_file_postfix', type=str,
					help='file name post fix for the written files or directories that are not completely written yet. Default is \"_TEMP_\"')

	# Optional argument
	parser.add_argument('--resample_Hz', type=float,
					help='An optional resample frequency for the written EDF data.')

	# Switch
	parser.add_argument('--zmax_lite', action='store_true',
					help='Switch to indicate if the device is a ZMax lite version and not all channels have to be included')

	# Switch
	parser.add_argument('--read_only_EEG', action='store_true',
					help='Switch to indicate if only "EEG L" and "EEG R" channels should be read in. --zmax_lite switch is invalidated by this')

	# Switch
	parser.add_argument('--read_only_EEG_BATT', action='store_true',
					help='Switch to indicate if only "EEG L" and "EEG R" and "BATT" channels should be read in. --zmax_lite switch and --read_only_EEG is invalidated by this')

	# Switch
	parser.add_argument('--no_write', action='store_true',
					help='Switch to indicate if files should be written out or not.')

	# Switch
	parser.add_argument('--no_overwrite', action='store_true',
					help='Switch to indicate if files should be overwritten if existent')

	# Switch
	parser.add_argument('--no_summary_csv', action='store_true',
					help='Switch to indicate if a summary file should not be written')

	# Switch
	parser.add_argument('--no_file_hashing', action='store_true',
					help='Switch to indicate if the file hash (i.e. MD5 sum) should be calculated (to compare if data is the same for same hash)')

	# Switch
	parser.add_argument('--no_signal_hashing', action='store_true',
					help='Switch to indicate if the signal data hash should be calculated (to compare if data is the same for same hash)')

	# Switch
	parser.add_argument('--exclude_empty_channels', action='store_true',
					help='Switch to indicate if channels that are constant (i.e. empty and likely not recorded) should be excluded/dropped. Requires some more computation time but saves space in case it is not zipped.')

	# Switch
	parser.add_argument('--write_zip', action='store_true',
					help='Switch to indicate if the output edfs should be zipped in one .zip file')

	args = parser.parse_args()

	parent_dir_paths = [pathlib.Path().resolve()] # the current working directory
	if args.parent_dir_paths is not None:
		parent_dir_paths = args.parent_dir_paths

	write_redirection_path = None
	if args.write_redirection_path is not None:
		write_redirection_path = args.write_redirection_path

	exclude_empty_channels = False
	if args.exclude_empty_channels is not None:
		exclude_empty_channels = args.exclude_empty_channels

	isliteversion = False
	if args.zmax_lite is not None:
		isliteversion = args.zmax_lite

	read_only_EEG = False
	if args.read_only_EEG is not None:
		read_only_EEG = args.read_only_EEG

	read_only_EEG_BATT = False
	if args.read_only_EEG_BATT is not None:
		read_only_EEG_BATT = args.read_only_EEG_BATT
	
	write_zip = False
	if args.write_zip is not None:
		write_zip = args.write_zip

	read_zip = False
	if args.read_zip is not None:
		read_zip = args.read_zip

	zipfile_match_string = ''
	if args.zipfile_match_string is not None:
		zipfile_match_string = args.zipfile_match_string

	zipfile_nonmatch_string = ''
	if args.zipfile_nonmatch_string is not None:
		zipfile_nonmatch_string = args.zipfile_nonmatch_string

	no_write = False
	if args.no_write is not None:
		no_write = args.no_write

	no_overwrite = False
	if args.no_overwrite is not None:
		no_overwrite = args.no_overwrite

	no_summary_csv = False
	if args.no_summary_csv is not None:
		no_summary_csv = args.no_summary_csv

	no_file_hashing = False
	if args.no_file_hashing is not None:
		no_file_hashing = args.no_file_hashing

	no_signal_hashing = False
	if args.no_signal_hashing is not None:
		no_signal_hashing = args.no_signal_hashing

	file_hashing = not no_file_hashing
	signal_hashing = not no_signal_hashing

	zmax_ppgparser = False
	if args.zmax_ppgparser is not None:
		zmax_ppgparser = args.zmax_ppgparser

	zmax_ppgparser_exe_path = application_path + os.sep + 'PPGParser.exe' # in the current working directory
	if args.zmax_ppgparser_exe_path is not None:
		zmax_ppgparser_exe_path = args.zmax_ppgparser_exe_path

	zmax_ppgparser_timeout_seconds = None # in seconds
	if args.zmax_ppgparser_timeout_seconds is not None:
		zmax_ppgparser_timeout_seconds = args.zmax_ppgparser_timeout_seconds

	zmax_eegcleaner = False
	if args.zmax_eegcleaner is not None:
		zmax_eegcleaner = args.zmax_eegcleaner

	zmax_eegcleaner_exe_path = application_path + os.sep + 'EDFCleaner.exe' # in the current working directory
	if args.zmax_eegcleaner_exe_path is not None:
		zmax_eegcleaner_exe_path = args.zmax_eegcleaner_exe_path

	zmax_eegcleaner_timeout_seconds = None # in seconds
	if args.zmax_eegcleaner_timeout_seconds is not None:
		zmax_eegcleaner_timeout_seconds = args.zmax_eegcleaner_timeout_seconds

	zmax_edfjoin = False
	if args.zmax_edfjoin is not None:
		zmax_edfjoin = args.zmax_edfjoin

	zmax_edfjoin_exe_path = application_path + os.sep + 'EDFJoin.exe' # in the current working directory
	if args.zmax_edfjoin_exe_path is not None:
		zmax_edfjoin_exe_path = args.zmax_edfjoin_exe_path

	zmax_edfjoin_timeout_seconds = None # in seconds
	if args.zmax_edfjoin_timeout_seconds is not None:
		zmax_edfjoin_timeout_seconds = args.zmax_edfjoin_timeout_seconds

	zmax_raw_hyp_file = False
	if args.zmax_raw_hyp_file is not None:
		zmax_raw_hyp_file = args.zmax_raw_hyp_file

	zmax_hdrecorder_exe_path = application_path + os.sep + 'HDRecorder.exe' # in the current working directory
	if args.zmax_hdrecorder_exe_path is not None:
		zmax_hdrecorder_exe_path = args.zmax_hdrecorder_exe_path

	hdrecorder_SDConvert_folder_path = fileparts(zmax_hdrecorder_exe_path)[0] + os.sep + 'SDConvert'

	zmax_hdrecorder_timeout_seconds = None # in seconds
	if args.zmax_hdrecorder_timeout_seconds is not None:
		zmax_hdrecorder_timeout_seconds = args.zmax_hdrecorder_timeout_seconds

	zmax_raw_hyp_keep_edf = False
	if args.zmax_raw_hyp_keep_edf is not None:
		zmax_raw_hyp_keep_edf = args.zmax_raw_hyp_keep_edf

	resample_Hz = None
	if args.resample_Hz is not None:
		resample_Hz = args.resample_Hz

	write_name_postfix = "_merged"
	if args.write_name_postfix is not None:
		write_name_postfix = args.write_name_postfix

	temp_file_postfix = "_TEMP_"
	if args.temp_file_postfix is not None:
		temp_file_postfix = args.temp_file_postfix

	#if len(sys.argv) != 3:
	#	print('expecting path to a parent folders with zmax edfs converted from HDrecorder as the only argument')
	#	exit(0)

	only_post_process_csv_summary_file = False
	if not no_summary_csv:
		filepath_csv_summary_file =  application_path + os.sep + 'zmax_edf_merge_converter_summary_' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S%f") + '.csv'

	#parentdirpath = sys.argv[1]
	nFileProcessed = 0
	processing_started = False
	for parentdirpath in parent_dir_paths:
		read_zip_temp = read_zip
		zmax_raw_hyp_file_temp = zmax_raw_hyp_file
		do_find = True
		filepath_list = []
		if os.path.isfile(parentdirpath):
			p, n, e = fileparts(parentdirpath)
			if e.lower() == ".zip":
				read_zip_temp = True
				filepath_list = [parentdirpath]
				do_find = False
			elif e.lower() == ".hyp":
				read_zip_temp = False
				zmax_raw_hyp_file_temp = True
				filepath_list = [parentdirpath]
				do_find = False
			elif (e.lower() == ".csv") and (len(parent_dir_paths) == 1):
				filepath_csv_summary_file = parentdirpath
				only_post_process_csv_summary_file = True
				do_find = False
				break
			else:
				#filepath_list = [] # do not process
				continue
				#parentdirpath = p
			#if e.lower() != ".edf":
			#	read_zip_temp = False
			#	parentdirpath = p
		else:
			try:
				parentdirpath = dir_path(parentdirpath)
			except NotADirectoryError:
				print("argument '%s' is not a directory" %parentdirpath)
				continue #exit(0)

			if parentdirpath is None:
				print("argument '%s' is not parsable" %parentdirpath)
				continue #exit(0)

			if do_find:
				print("Finding file paths...")
				filepath_list = find_zmax_files(parentdirpath, readzip=read_zip_temp, zipfile_match_string=zipfile_match_string, zipfile_nonmatch_string=zipfile_nonmatch_string, find_hyp_files=zmax_raw_hyp_file_temp)

		print("FOUND %d matching file paths " % len(filepath_list))
		for iFn, fn in enumerate(filepath_list):
			print("%d: %s" % (iFn, fn))

		if len(filepath_list) < 1:
			print("no zmax files found")
			#exit(0)

		number_of_conversions = len(filepath_list)
		for i, filepath_outer in enumerate(filepath_list):
			rm_dir_list = []
			temp_dir_needs_removal = False
			filepath_ori = filepath_outer
			cleanup_tempdir_hyp_convert = False

			if not no_summary_csv:
				if not processing_started:
					csv_summary_file =  open(filepath_csv_summary_file, 'w', newline='')
					writer = csv.writer(csv_summary_file, delimiter=',', quoting=csv.QUOTE_NONNUMERIC, escapechar='\\')
					header_new = ['file_number', 'conversion_status', 'conversion_datetime', 'zmax_file_path_original_outer', 'zmax_file_path_original', 'hash_zmax_file_path_original_md5', 'converted_file_path', 'hash_converted_file_path_md5', 'rec_start_datetime', 'rec_stop_datetime', 'rec_duration_datetime', 'rec_duration_seconds', 'rec_duration_original_samples', 'rec_battery_at_end_voltage', 'hash_signals_before_conversion', 'hash_signals_after_conversion']
					writer.writerow(header_new)
					processing_started = True

			print("PROCESSING %d of %d: '%s' " % (i+1, number_of_conversions, filepath_outer))

			conversion_datetime = datetime.datetime.now()#.strftime("%Y-%m-%d %H:%M:%S:%f")
			read_zip_temp_reset = False
			filepaths = []
			export_filepaths = []
			if zmax_raw_hyp_file_temp and zmax_hdrecorder_exe_path is not None:
				print('ATTEMPT to convert .hyp file using HDRecorder: ' + filepath_outer)
				p, n, e = fileparts(filepath_outer)
				zmax_convert_edf_dir_path = p + os.sep + n
				filepath_list_hyps = []
				if read_zip_temp:
					read_zip_temp_reset = True
					try:
						temp_dir = safe_zip_dir_extract(filepath_outer)
						temp_dir_needs_removal = True
						fileendings = ('*.hyp', '*.HYP')
						for fileending in fileendings:
							filepath_list_hyps.extend(glob.glob(temp_dir.name + os.sep + "**" + os.sep + fileending, recursive=True))
						#safe_zip_dir_cleanup(temp_dir)
					except Exception:
						print(traceback.format_exc())
						print('FAILED to convert the zipped hyp files in ' + filepath_outer)
						break
				else:
					filepath_list_hyps.extend([filepath_outer])
				try:
					for fp in filepath_list_hyps:
						exec_string =  "\"" + zmax_hdrecorder_exe_path + "\"" + " -conv " + "\"" + fp + "\""
						subprocess.run(exec_string, shell=False, timeout=zmax_hdrecorder_timeout_seconds)

						if (fileparts(filepath_outer)[2].lower() == ".zip") and read_zip_temp:
							pp, nn, ee = fileparts(zmax_convert_edf_dir_path + fp.replace(temp_dir.name,""))
							zmax_convert_edf_dir_path_temp = pp + os.sep + nn + temp_file_postfix
						else:
							zmax_convert_edf_dir_path_temp = zmax_convert_edf_dir_path + temp_file_postfix
						#os.makedirs(zmax_convert_edf_dir_path_temp, exist_ok=True)

						if write_redirection_path is not None:
							parentdirpath_temp = get_dir_path(parentdirpath)
							indFound = zmax_convert_edf_dir_path_temp.find(parentdirpath_temp)
							if indFound >= 0:
								zmax_convert_edf_dir_path_temp = write_redirection_path + zmax_convert_edf_dir_path_temp[(indFound+len(parentdirpath_temp)):]
								path_create(zmax_convert_edf_dir_path_temp, isFile=False)
						try:
							shutil.rmtree(zmax_convert_edf_dir_path_temp)
						except Exception:
							print('FAILED TO DELETE THE LEFT TEMPORARY DIRECTORY: %s' % zmax_convert_edf_dir_path_temp)
							print(traceback.format_exc())
						dirpath_add = shutil.move(hdrecorder_SDConvert_folder_path, zmax_convert_edf_dir_path_temp)
						filepath_add = dirpath_add + os.sep + 'EEG L.edf'
						fnp, fnn, fne = fileparts(fp)
						if fileparts(filepath_outer)[2].lower() == ".zip" and read_zip_temp:
							export_filepath_inner_hyp = pp + os.sep + nn + write_name_postfix
						else:
							export_filepath_inner_hyp = p + os.sep + n + write_name_postfix
						filepaths.append(filepath_add)
						export_filepaths.append(export_filepath_inner_hyp)
						cleanup_tempdir_hyp_convert = True
						rm_dir_list.extend([hdrecorder_SDConvert_folder_path, dirpath_add])
				except Exception:
					print(traceback.format_exc())
					print('FAILED to convert the hyp file ' + filepath_outer)
					break
			else:
				filepaths.append(filepath_outer)

			for iFilePath, filepath in enumerate(filepaths):
				md5_signal_hash_before_conversion = 'not_computed'
				md5_file_original_hash = 'not_computed'
				md5_signal_hash_after_conversion = 'not_computed'
				md5_file_converted_hash = 'not_computed'
				rec_start_datetime = 'not_retrieved'
				rec_stop_datetime = 'not_retrieved'
				rec_duration_datetime = 'not_retrieved'
				rec_battery_at_end = 'not_retrieved'
				conversion_status = 'not_converted'
				export_filepath_final = ''
				rec_duration_seconds = None
				rec_n_samples = None
				nFileProcessed += 1
				path, name, extension = fileparts(filepath)
				parentfoldername = os.path.basename(path)
				pathup, nametmp, extensiontmp = fileparts(path)

				format = "zmax_edf"
				zmax_edfjoin_move_path_subdir = None

				rm_dir_list_inner = []

				drop_channels = []
				if isliteversion:
					drop_channels = ['BODY TEMP', 'LIGHT', 'NASAL L', 'NASAL R', 'NOISE', 'OXY_DARK_AC', 'OXY_DARK_DC', 'OXY_R_AC', 'OXY_R_DC', 'RSSI', 'PARSED_NASAL R', 'PARSED_NASAL L', 'PARSED_OXY_R_AC', 'PARSED_HR_r', 'PARSED_HR_r_strength']
				if read_only_EEG:
					drop_channels = ['BATT', 'BODY TEMP', 'dX', 'dY', 'dZ', 'LIGHT', 'NASAL L', 'NASAL R', 'NOISE', 'OXY_DARK_AC', 'OXY_DARK_DC', 'OXY_IR_AC', 'OXY_IR_DC', 'OXY_R_AC', 'OXY_R_DC', 'RSSI', 'PARSED_NASAL R', 'PARSED_OXY_IR_AC', 'PARSED_NASAL L', 'PARSED_HR_r', 'PARSED_HR_r_strength', 'PARSED_OXY_R_AC', 'PARSED_HR_ir', 'PARSED_HR_ir_strength']
				if read_only_EEG_BATT:
					drop_channels = ['BODY TEMP', 'dX', 'dY', 'dZ', 'LIGHT', 'NASAL L', 'NASAL R', 'NOISE', 'OXY_DARK_AC', 'OXY_DARK_DC', 'OXY_IR_AC', 'OXY_IR_DC', 'OXY_R_AC', 'OXY_R_DC', 'RSSI', 'PARSED_NASAL R', 'PARSED_OXY_IR_AC', 'PARSED_NASAL L', 'PARSED_HR_r', 'PARSED_HR_r_strength', 'PARSED_OXY_R_AC', 'PARSED_HR_ir', 'PARSED_HR_ir_strength']
				try:
					if export_filepaths:
						export_filepath = export_filepaths[iFilePath]
					else:
						if read_zip_temp:
							export_filepath = path + os.sep + name + write_name_postfix
						else:
							export_filepath = pathup + os.sep +  parentfoldername + write_name_postfix

					if write_redirection_path is not None:
						parentdirpath_temp = get_dir_path(parentdirpath)
						indFound = export_filepath.find(parentdirpath_temp)
						if indFound >= 0:
							export_filepath = write_redirection_path + export_filepath[(indFound+len(parentdirpath_temp)):]
							#if write_zip:
							path_create(export_filepath, isFile=True)
							#else:
							#	path_create(export_filepath,isFile=True)

					export_filepath_unfinished = export_filepath + temp_file_postfix

					if write_zip:
						export_filepath_final_to_rename = export_filepath_unfinished + ".zip"
					else:
						export_filepath_final_to_rename = export_filepath_unfinished + ".edf"

					export_filepath_final = export_filepath_final_to_rename.replace(temp_file_postfix,'')

					if no_overwrite:
						if os.path.exists(export_filepath_final):
							print('skipping file: %s' % export_filepath_final)
							continue

					#reading
					no_read = False
					if zmax_edfjoin:
						format = "zmax_edf_join"
						path_temp, name_temp, ext_temp = fileparts(export_filepath_final_to_rename)
						subdir_temp = path_temp + os.sep + temp_file_postfix
						finaldir_temp = path_temp + os.sep
						dir_path_create(subdir_temp)
						zmax_edfjoin_move_path_subdir = subdir_temp + os.sep + name_temp + ".edf"
						no_read = True
						if no_write:
							continue

					if read_zip_temp and (not read_zip_temp_reset):
						raw = read_edf_to_raw_zipped(filepath, format=format, zmax_ppgparser=zmax_ppgparser, zmax_ppgparser_exe_path=zmax_ppgparser_exe_path, zmax_ppgparser_timeout_seconds=zmax_ppgparser_timeout_seconds, zmax_eegcleaner=zmax_eegcleaner, zmax_eegcleaner_exe_path=zmax_eegcleaner_exe_path, zmax_eegcleaner_timeout_seconds=zmax_eegcleaner_timeout_seconds, zmax_edfjoin_exe_path=zmax_edfjoin_exe_path, zmax_edfjoin_timeout_seconds=zmax_edfjoin_timeout_seconds, zmax_edfjoin_keep=False, zmax_edfjoin_move_path=zmax_edfjoin_move_path_subdir, no_read=no_read, drop_zmax=drop_channels)
					else:
						raw = read_edf_to_raw(filepath, format=format, zmax_ppgparser=zmax_ppgparser, zmax_ppgparser_exe_path=zmax_ppgparser_exe_path, zmax_ppgparser_timeout_seconds=zmax_ppgparser_timeout_seconds, zmax_eegcleaner=zmax_eegcleaner, zmax_eegcleaner_exe_path=zmax_eegcleaner_exe_path, zmax_eegcleaner_timeout_seconds=zmax_eegcleaner_timeout_seconds, zmax_edfjoin_exe_path=zmax_edfjoin_exe_path, zmax_edfjoin_timeout_seconds=zmax_edfjoin_timeout_seconds, zmax_edfjoin_keep=False, zmax_edfjoin_move_path=zmax_edfjoin_move_path_subdir, no_read=no_read, drop_zmax = drop_channels)



					print("READ %d of %d: '%s' " % (i+1, number_of_conversions, filepath))
					conversion_status = 'read_in'


					if zmax_edfjoin:
						zmax_edfjoin_move_path_subdir = raw
						if raw is None:
							continue
						joined_filepath_moved_to_rename = zmax_edfjoin_move_path_subdir.replace(temp_file_postfix+os.sep,'')
						#joined_filepath_moved_final = joined_filepath_moved_final.replace(temp_file_postfix,'')
						try:
							if not write_zip:
								export_filepath_final_to_rename = shutil.move(zmax_edfjoin_move_path_subdir, joined_filepath_moved_to_rename)
							else:
								path_tmp, name_tmp, ext_tmp = fileparts(zmax_edfjoin_move_path_subdir)
								name_tmp_final = name_tmp.replace(temp_file_postfix,'')
								joined_filepath_moved_final_subdir_final = path_tmp + os.sep + name_tmp_final + ext_tmp
								joined_filepath_moved_final_subdir_final = shutil.move(zmax_edfjoin_move_path_subdir, joined_filepath_moved_final_subdir_final)
								path_temp, name_temp, ext_temp = fileparts(joined_filepath_moved_final_subdir_final)
								joined_filepath_moved_final_subdir_final_zip = path_temp + os.sep + name_temp + temp_file_postfix + '.zip'
								joined_filepath_moved_final_subdir_final_zip = zip_file(joined_filepath_moved_final_subdir_final, joined_filepath_moved_final_subdir_final_zip, deletefile=True, compresslevel=6)
								#os.remove(joined_filepath_moved_final_subdir_final)
								export_filepath_final_to_rename = joined_filepath_moved_final_subdir_final_zip.replace(temp_file_postfix+os.sep,'')
								shutil.move(joined_filepath_moved_final_subdir_final_zip, export_filepath_final_to_rename)
								try:
									shutil.rmtree(path_tmp, ignore_errors=True)
								except Exception:
									rm_dir_list_inner.extend([path_tmp])
									print('FAILED TO remove temporary folder %s for filepath %s but will try again once more later.' % (path_tmp, filepath))
									print(traceback.format_exc())
						except Exception:
							print('FAILED TO MOVE or ZIP THE file %s to %s or its zipped form.' % (filepath, joined_filepath_moved_to_rename))
							print(traceback.format_exc())
					else:
						# data hashing pre
						if signal_hashing:
							print("HASHING SIGNAL OF FILE %d of %d: '%s' " % (i+1, number_of_conversions, filepath))
							md5_signal_hash_before_conversion = get_raw_data_hash(raw, hash_function=hashlib.md5)
							print("MD5 SIGNAL HASH: " + md5_signal_hash_before_conversion)
							#raw_short_ori = raw.copy()
							#raw_short_ori.crop(tmin=0, tmax=60*4)
							#md5_signal_hash_before_conversion_short_ori = get_raw_data_hash(raw_short_ori, hash_function=hashlib.md5)
							#raw_short_crop = raw.copy()
							#raw_short_crop.crop(tmin=2.671875, tmax=60*4)
							#md5_signal_hash_before_conversion_short_crop = get_raw_data_hash(raw_short_crop, hash_function=hashlib.md5)

						rec_start_datetime = raw.info['meas_date']
						rec_stop_datetime = rec_start_datetime + datetime.timedelta(seconds=(raw._last_time - raw._first_time))
						rec_duration_datetime = datetime.timedelta(seconds=(raw._last_time - raw._first_time))
						rec_duration_seconds = rec_duration_datetime.total_seconds()
						rec_n_samples = raw.n_times
						rec_battery_at_end = raw_zmax_data_quality(raw)

						if exclude_empty_channels:
							flat_channel_names = []
							for iCh, ch_name in enumerate(raw.info['ch_names']):
								ch_name = raw.info['ch_names'][iCh]
								nNotFlat = numpy.count_nonzero(raw._data[iCh]-statistics.median(raw._data[iCh])) # this is fastest so far
								if nNotFlat <= 10:
									flat_channel_names.append(ch_name)
							raw.drop_channels(flat_channel_names)

						if resample_Hz is not None:
							raw = raw.resample(resample_Hz)

						sampling_rate_final_Hz = raw.info['sfreq']

						# file hashing original
						if file_hashing:
							print("HASHING FILE %d of %d: '%s' " % (i+1, number_of_conversions, filepath))
							md5_file_original_hash = get_file_hash(filepath, chunk_size_bytes=65536, hash_function=hashlib.md5)
							print("MD5 FILE HASH: " + md5_file_original_hash)

						# data hashing post
						if signal_hashing:
							print("HASHING SIGNAL (after conversion) OF FILE %d of %d: '%s' " % (i+1, number_of_conversions, filepath))
							md5_signal_hash_after_conversion = get_raw_data_hash(raw, hash_function=hashlib.md5)
							print("MD5 SIGNAL HASH: " + md5_signal_hash_after_conversion)

						conversion_status = 'read_in_processed'

					#writing
					if not no_write:
						# check again just before writing
						if no_overwrite:
							if os.path.exists(export_filepath_final):
								print('skipping file: %s' % export_filepath_final)
								continue
						print("Attempting to write %d of %d: '%s' " % (i+1, number_of_conversions, export_filepath_final))
						if not zmax_edfjoin:
							if write_zip:
								export_filepath_final_to_rename_2 = write_raw_to_edf_zipped(raw, export_filepath_final_to_rename, edf_filename=export_filepath_final, format="zmax_edf") # treat as a speacial zmax read EDF for export
							else:
								export_filepath_final_to_rename_2 = write_raw_to_edf(raw, export_filepath_final_to_rename, format="zmax_edf")  # treat as a speacial zmax read EDF for export
							conversion_status = 'read_in_processed_written_temp'
						try:
							# check again just before writing
							if no_overwrite:
								os.rename(export_filepath_final_to_rename, export_filepath_final)
							else:
								if os.path.exists(export_filepath_final):
									try:
										os.remove(export_filepath_final)
									except FileNotFoundError:
										pass
								shutil.move(export_filepath_final_to_rename, export_filepath_final)
							print("WROTE successfully %d of %d: '%s' " % (i+1, number_of_conversions, export_filepath_final))
							conversion_status = 'read_in_processed_written_converted'
							# file hashing converted
							if file_hashing:
								print("HASHING FILE after conversion %d of %d: '%s' " % (i+1, number_of_conversions, filepath))
								md5_file_converted_hash = get_file_hash(export_filepath_final, chunk_size_bytes=65536, hash_function=hashlib.md5)
								print("MD5 FILE after conversion HASH: " + md5_file_converted_hash)
						except:
							print('FAILED TO RENAME FINAL FILE %s FROM TEMPORARY FILE' % (export_filepath_final))
							print(traceback.format_exc())
							#finally remove the temporary file if exists
						try:
							try:
								os.remove(export_filepath_final_to_rename)
							except FileNotFoundError:
								pass
						except:
							print('FAILED TO DELETE THE LEFT TEMPORARY FILE: %s' % export_filepath_final_to_rename)
							print(traceback.format_exc())

				except Exception as e:
					print(traceback.format_exc())
					print("FAILED %d of %d: '%s' " % (i+1, number_of_conversions, filepath))

				for dp in rm_dir_list_inner:
					try:
						shutil.rmtree(dp)
					except Exception:
						print('FAILED TO DELETE THE LEFT TEMPORARY DIRECTORY: %s' % dp)
						print(traceback.format_exc())

				# write to summary
				if (not no_summary_csv) and processing_started:
					row_new = [nFileProcessed, conversion_status, conversion_datetime, filepath_outer, filepath, md5_file_original_hash, export_filepath_final, md5_file_converted_hash, rec_start_datetime, rec_stop_datetime, rec_duration_datetime, rec_duration_seconds, rec_n_samples, rec_battery_at_end, md5_signal_hash_before_conversion, md5_signal_hash_after_conversion]
					writer.writerow(row_new)
					csv_summary_file.flush()

			if cleanup_tempdir_hyp_convert and (not zmax_raw_hyp_keep_edf):
				for dp in rm_dir_list:
					try:
						shutil.rmtree(dp)
					except Exception:
						print('FAILED TO DELETE THE LEFT TEMPORARY DIRECTORY: %s' % dp)
						print(traceback.format_exc())

			if temp_dir_needs_removal:
				try:
					safe_zip_dir_cleanup(temp_dir)
				except:
					print('FAILED TO DELETE THE LEFT TEMPORARY DIRECTORY: %s' % temp_dir)
					print(traceback.format_exc())

	# close summary csv file again
	if (not no_summary_csv) and (not only_post_process_csv_summary_file) and processing_started:
		csv_summary_file.close()
	if (not no_summary_csv) or only_post_process_csv_summary_file:
		df_csv_in = pandas.read_csv(filepath_csv_summary_file, quoting=csv.QUOTE_NONNUMERIC)
		df_csv_in.reset_index()  # make sure indexes pair with number of rows

		df_csv_in_by_n_samples = df_csv_in.sort_values(by=['rec_duration_original_samples'],ascending=True)
		df_csv_in_by_n_samples["duplicates_in_duration"] = numpy.nan
		df_len = len(df_csv_in_by_n_samples.index)
		df_csv_in_by_n_samples.reset_index()
		for iRow in range(0,df_len,1):
			row = df_csv_in_by_n_samples.iloc[iRow, :]
			ns = row['rec_duration_original_samples']
			if (ns is None) or ns is numpy.nan:
				break
			for iRow2 in range(iRow+1,df_len,1):
				row2 = df_csv_in_by_n_samples.iloc[iRow2, :]
				ns2 = row2['rec_duration_original_samples']
				if ns2 > (ns + 5*256):
					break
				elif ns2 == ns:
					#print(row.zmax_file_path_original)
					#print(row2.zmax_file_path_original)
					df_csv_in_by_n_samples.iloc[iRow, df_csv_in_by_n_samples.columns.get_loc("duplicates_in_duration")] = row2["file_number"]
					df_csv_in_by_n_samples.iloc[iRow2, df_csv_in_by_n_samples.columns.get_loc("duplicates_in_duration")] = row["file_number"]
					break

		df_csv_in = df_csv_in_by_n_samples.sort_values(by=['file_number'],ascending=True)


		df_csv_in_by_n_samples = df_csv_in.sort_values(by=['rec_duration_original_samples'],ascending=True)
		df_csv_in_by_n_samples["duplicates_in_duration_different_conversion"] = numpy.nan
		df_len = len(df_csv_in_by_n_samples.index)
		df_csv_in_by_n_samples.reset_index()
		for iRow in range(0,df_len,1):
			row = df_csv_in_by_n_samples.iloc[iRow, :]
			ns = row['rec_duration_original_samples']
			if (ns is None) or ns is numpy.nan:
				break
			for iRow2 in range(iRow+1,df_len,1):
				row2 = df_csv_in_by_n_samples.iloc[iRow2, :]
				ns2 = row2['rec_duration_original_samples']
				if ns2 > (ns + 5*256):
					break
				elif ns2 == (ns + 5*256):
					#print(row.zmax_file_path_original)
					#print(row2.zmax_file_path_original)
					df_csv_in_by_n_samples.iloc[iRow, df_csv_in_by_n_samples.columns.get_loc("duplicates_in_duration_different_conversion")] = row2["file_number"]
					df_csv_in_by_n_samples.iloc[iRow2, df_csv_in_by_n_samples.columns.get_loc("duplicates_in_duration_different_conversion")] = row["file_number"]
					break
		df_csv_in = df_csv_in_by_n_samples.sort_values(by=['file_number'],ascending=True)

		df_csv_in_by_hash = df_csv_in.sort_values(by=['hash_zmax_file_path_original_md5'],ascending=True)
		df_csv_in_by_hash["duplicates_in_hash_zmax_file_path_original_md5"] = numpy.nan
		df_len = len(df_csv_in_by_hash.index)
		df_csv_in_by_hash.reset_index()
		for iRow in range(0,df_len,1):
			row = df_csv_in_by_hash.iloc[iRow, :]
			hash_string = row['hash_zmax_file_path_original_md5']
			if (hash_string is None) or (hash_string == 'not_computed'):
				break
			for iRow2 in range(iRow+1,df_len,1):
				row2 = df_csv_in_by_hash.iloc[iRow2, :]
				hash_string2 = row2['hash_zmax_file_path_original_md5']
				if hash_string2 == hash_string:
					df_csv_in_by_hash.iloc[iRow, df_csv_in_by_hash.columns.get_loc("duplicates_in_hash_zmax_file_path_original_md5")] = row2["file_number"]
					df_csv_in_by_hash.iloc[iRow2, df_csv_in_by_hash.columns.get_loc("duplicates_in_hash_zmax_file_path_original_md5")] = row["file_number"]
					break
		df_csv_in = df_csv_in_by_hash.sort_values(by=['file_number'],ascending=True)

		df_csv_in_by_hash = df_csv_in.sort_values(by=['hash_converted_file_path_md5'],ascending=True)
		df_csv_in_by_hash["duplicates_in_hash_converted_file_path_md5"] = numpy.nan
		df_len = len(df_csv_in_by_hash.index)
		df_csv_in_by_hash.reset_index()
		for iRow in range(0,df_len,1):
			row = df_csv_in_by_hash.iloc[iRow, :]
			hash_string = row['hash_converted_file_path_md5']
			if (hash_string is None) or (hash_string == 'not_computed'):
				break
			for iRow2 in range(iRow+1,df_len,1):
				row2 = df_csv_in_by_hash.iloc[iRow2, :]
				hash_string2 = row2['hash_converted_file_path_md5']
				if hash_string2 == hash_string:
					df_csv_in_by_hash.iloc[iRow, df_csv_in_by_hash.columns.get_loc("duplicates_in_hash_converted_file_path_md5")] = row2["file_number"]
					df_csv_in_by_hash.iloc[iRow2, df_csv_in_by_hash.columns.get_loc("duplicates_in_hash_converted_file_path_md5")] = row["file_number"]
					break
		df_csv_in = df_csv_in_by_hash.sort_values(by=['file_number'],ascending=True)


		df_csv_in_by_hash = df_csv_in.sort_values(by=['hash_signals_before_conversion'],ascending=True)
		df_csv_in_by_hash["duplicates_in_hash_signals_before_conversion"] = numpy.nan
		df_len = len(df_csv_in_by_hash.index)
		df_csv_in_by_hash.reset_index()
		for iRow in range(0,df_len,1):
			row = df_csv_in_by_hash.iloc[iRow, :]
			hash_string = row['hash_signals_before_conversion']
			if (hash_string is None) or (hash_string == 'not_computed'):
				break
			for iRow2 in range(iRow+1,df_len,1):
				row2 = df_csv_in_by_hash.iloc[iRow2, :]
				hash_string2 = row2['hash_signals_before_conversion']
				if hash_string2 == hash_string:
					df_csv_in_by_hash.iloc[iRow, df_csv_in_by_hash.columns.get_loc("duplicates_in_hash_signals_before_conversion")] = row2["file_number"]
					df_csv_in_by_hash.iloc[iRow2, df_csv_in_by_hash.columns.get_loc("duplicates_in_hash_signals_before_conversion")] = row["file_number"]
					break
		df_csv_in = df_csv_in_by_hash.sort_values(by=['file_number'],ascending=True)

		df_csv_in_by_hash = df_csv_in.sort_values(by=['hash_signals_after_conversion'],ascending=True)
		df_csv_in_by_hash["duplicates_in_hash_signals_after_conversion"] = numpy.nan
		df_len = len(df_csv_in_by_hash.index)
		df_csv_in_by_hash.reset_index()
		for iRow in range(0,df_len,1):
			row = df_csv_in_by_hash.iloc[iRow, :]
			hash_string = row['hash_signals_after_conversion']
			if (hash_string is None) or (hash_string == 'not_computed'):
				break
			for iRow2 in range(iRow+1,df_len,1):
				row2 = df_csv_in_by_hash.iloc[iRow2, :]
				hash_string2 = row2['hash_signals_after_conversion']
				if hash_string2 == hash_string:
					df_csv_in_by_hash.iloc[iRow, df_csv_in_by_hash.columns.get_loc("duplicates_in_hash_signals_after_conversion")] = row2["file_number"]
					df_csv_in_by_hash.iloc[iRow2, df_csv_in_by_hash.columns.get_loc("duplicates_in_hash_signals_after_conversion")] = row["file_number"]
					break
		df_csv_in = df_csv_in_by_hash.sort_values(by=['file_number'],ascending=True)

		df_csv_in.to_csv(filepath_csv_summary_file, mode='w', index=False, header=True, quoting=csv.QUOTE_NONNUMERIC)

		print('finished')
