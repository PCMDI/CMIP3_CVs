#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 13:44:34 2022

PJD 30 Sep 2022     - Written to reorganize INM PMIP CMIP6 data removing duplication version dirs
PJD  5 Oct 2022     - updated to gather CMIP3 path information
PJD  6 Oct 2022     - updated to identify all bad files/dirs (replicate these into their own CMIP3/bad subdir tree)
PJD  6 Oct 2022     - Added badRoots and excludeDirs - to limit bombs
PJD  7 Oct 2022     - Added "PST" test to NCAR files (alongside "MDT")
PJD  8 Oct 2022     - Added ds.drop_vars call; add cmorVersion grab
PJD  9 Oct 2022     - Augmented NCAR timezones; cmorVersion to str type
PJD 10 Oct 2022     - Deal with edge case where CMOR was used to rewrite and CDO rewrote the rewritten /p/css03/esgf_publish/cmip3/ipcc/cfmip/2xco2/atm/mo/rsut/mpi_echam5/run1/rsut_CF1.nc
PJD 12 Oct 2022     - Added noDateFileCount/List - separate non-bad files?
PJD 13 Oct 2022     - Added try around file opens
PJD 14 Oct 2022     - Updated json output names to optimize ordering !_
PJD 29 Jun 2023     - Updated with getSha256
PJD 30 Jun 2023     - Updated to scan additional global_atts: contact, experiment_id, institution, realization, source, table_id, comment
PJD 30 Jun 2023     - Added getFileSize
PJD 30 Jun 2023     - Removed table_id as this has file generation date/time - will provide erronous timestamp
PJD 11 Jul 2023     - Added os.stat().st_mtime as these appear to be reasonable estimates
PJD 11 Jul 2023     - Added /p/css03/esgf_publish/cmip3/ipcc/cmip5/ozone/ to exclude dirs "bad"
                    TODO: generalize for global attributes that serve CMIP5 and 6 datasets
                    TODO: add time start/stop to fileNames that exclude them
                    TODO: table mappings O1 = Omon?, O1e?

@author: durack1
"""

import datetime
import hashlib
import json
import os
import re

# import shutil
import xarray as xr
from xcdat import open_dataset
import pdb

# import sys
# import time

# %% function defs

"""
def copyStuff(root, dirs, destDir, vers):
    # deal with multi-dir or single dir
    if not vers:
        fullPath = os.path.join(root, dirs[0])
        shutil.copytree(fullPath, fullPath.replace(
            "CMIP6", destDir))  # start copying
        return
    else:
        dirWritten = False
        for dirCount, dirPath in enumerate(dirs):
            fullPath = os.path.join(root, dirPath)
            fileList = os.listdir(fullPath)
            for fileCount, fileName in enumerate(fileList):
                srcPath = os.path.join(root, dirPath)
                src = os.path.join(root, dirPath, fileName)
                dstPath = os.path.join(root.replace(
                    "CMIP6", destDir), dirs[0])
                dst = os.path.join(root.replace(
                    "CMIP6", destDir), dirs[0], fileName)
                print("srcPath:", srcPath)
                print("src:", src)
                if not dirWritten:
                    # copy once
                    shutil.copytree(srcPath, dstPath)
                    dirWritten = True
                    continue  # add files to dir from second verDir
                if 'nc.2xYTPm' in fileName:
                    print("nc.2xYTPm")
                    print("fileName:", fileName, "skipped")
                    continue
                shutil.copy2(src, dst)
                print("dstPath:", dstPath)
                print("dst:", dst)
        return
    return
"""


def checkDate(dateStr):
    # assume 2022-10-05 format
    y, m, d = dateStr.split("-")
    if not 2003 <= int(y) <= 2008:
        print("year invalid:", y)
        return None
    if not 1 <= int(m) <= 12:
        print("month invalid:", m)
        return None
    if not 1 <= int(d) <= 31:
        print("day invalid:", d)
        return None

    return dateStr


def fixFunc(fixStr, fixStrInfo):
    def fix(ds):
        print(fixStrInfo)
        exec(fixStr)  # ds.time.encoding["units"] = "days since 2001-1-1"

        return ds

    return fix


def getFileStats(filePath):
    if os.path.isfile(filePath):
        fileStats = os.stat(filePath)
        fileSizeBytes = fileStats.st_size
        fileModTime = datetime.datetime.fromtimestamp(fileStats.st_mtime)
        fileModTime = makeDate(
            fileModTime.year, fileModTime.month, fileModTime.day, True
        )
    else:
        print("File:", filePath, "not a valid file")
        fileSizeBytes = 0.0
        fileModTime = 0.0

    return fileSizeBytes, fileModTime


def getSha256(filePath, print=False):
    with open(filePath, "rb") as f:
        bytes = f.read()  # read entire file as bytes
        readable_hash = hashlib.sha256(bytes).hexdigest()
        if print:
            print(readable_hash)

    return readable_hash


def getTimes(time):
    y = int(time.dt.year.data)
    m = int(time.dt.month.data)
    d = int(time.dt.day.data)
    dateStr = makeDate(y, m, d, check=False)

    return dateStr


def makeDate(year, month, day, check):
    date = "-".join([str(year), str(month), str(day)])
    # print("makeDate: date =", date)
    # pdb.set_trace()
    if check:
        date = checkDate(date)

    return date


def makeDRS(filePath, date):
    # source = cmip3/ipcc/data10/picntrl/ocn/mo/thetao/iap_fgoals1_0_g/run2/{files}.nc
    # target = CMIP3/DAMIP/NCAR/CCSM4/historicalMisc/r2i1p11/Omon/vo/gu/v20121128
    # hard-coded
    mipEra = "CMIP3"
    gridLabel = "gu"
    # filePath bits
    sourceBits = filePath.split("/")
    experiments = {"pdcntrl", "picntrl", "20c3m", "sresa1b", "sresa2", "sresb1"}
    # https://github.com/PCMDI/CMIP3_CVs/blob/main/src/writeJson.py#L63-L76
    experimentId = sourceBits[3]
    sourceId = sourceBits[7]
    # match up
    activityId = ["CMIP", "ScenarioMIP"]
    institutionId = []
    r = sourceBits[8].replace("run", "")
    ripf = "".join(["r", r, "i0p0f0"])  # switch X with runX
    tableId = ["mo", "da", "fixed"]
    varId = sourceBits[6]
    d = date.split("-")
    versionId = "".join(["v", d[0], d[1], d[2]])
    # composite
    destPath = os.path.join(
        mipEra,
        activityId,
        institutionId,
        sourceId,
        experimentId,
        ripf,
        tableId,
        varId,
        gridLabel,
        versionId,
    )

    return destPath


"""
def openData(filePath, fileName, ...):
    '''
    This function attempts to open datasets with additional arguments associated with file
    reads

    Returns
    -------
    None.

    '''
    try:
        # wrap so bombs are caught in except
        if (fixStr == None and badVars == None and badFile == None):
            fh = open_dataset(filePath, use_cftime=True)
        # Case bad root match, but not file
        elif fixStrInfo and (badFile != fileName and not badFile == ''):
            fh = open_dataset(filePath, use_cftime=True)
        # Case bad root match, AND file
        elif badVars and (fileName == badFile):  # badVars only
            print("badVars:", badVars)
            fh = (
                xr.open_dataset(
                    filePath, drop_variables=[badVars])
                .pipe(xr.decode_cf)
            )
        elif badFile == "":  # fixFunc for all files only - 9863
            print("badFile == ''")
            fh = (
                xr.open_dataset(filePath, decode_times=False)
                .pipe(fixFunc(fixStr, fixStrInfo))
                .pipe(xr.decode_cf)
            )
        # is there a need for fixFunc AND badVars?
        elif badVars == [] and (fileName == badFile):
            # print("elif3")
            # pdb.set_trace()
            badFileCount = badFileCount+1
            print("badFile; filePath:", filePath)
            cm3["!badFileCount"] = badFileCount
            cm3["!badFileList"][badFileCount] = filePath
            continue
    except:
        fileReadErrorCount = fileReadErrorCount+1
        print("fileReadError; filePath:", filePath)
        cm3["!fileReadErrorCount"] = fileReadErrorCount
        cm3["!fileReadError"][fileReadErrorCount] = filePath
        continue
"""

# %% deal with paths
# "/p/user_pub/climate_work/durack1/tmp/"
os.chdir("/home/durack1/git/CMIP3_CVs/src")
destDir = "CMIP3"  # "/a/"
# if os.path.exists(destDir):
#    shutil.rmtree(destDir)
# os.makedirs(destDir)

# %% create lookup lists
attList = [
    "cmor_version",
    "comment",
    "contact",
    "date",
    "experiment_id",
    "forcing",
    "history",
    "institution",
    "realization",
    "source",
]
# "creation_date","license","tracking_id", "table_id"
monList = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

# %% create exclude dirs
bad = {
    "/p/css03/esgf_publish/cmip3/ipcc/data3/sresa2/ice/mo/sic/ingv_echam4/run1": [
        "",
        "fix bad time:units 20O1-1-1",
        "ds.time.attrs['units'] = 'days since 2001-01-01'",
        [],
    ],
    "/p/css03/esgf_publish/cmip3/ipcc/data3/sresa2/ice/mo/sit/ingv_echam4/run1": [
        "",
        "fix bad time:units 20O1-1-1",
        "ds.time.attrs['units'] = 'days since 2001-01-01'",
        [],
    ],
    "/p/css03/esgf_publish/cmip3/ipcc/data8/picntrl/ocn/mo/rhopoto/ncar_ccsm3_0/run2": [
        "rhopoto_O1.PIcntrl_2.CCSM.ocnm.0585-01_cat_0589-12.nc",
        "drop bad time_bnds",
        "",
        ["time_bnds"],
    ],
    "/p/css03/esgf_publish/cmip3/ipcc/data16/sresa1b/atm/mo/rlds/mpi_echam5/run2": [
        "rlds_A1.nc",
        "drop bad time_bnds",
        "",
        ["time_bnds"],
    ],
    "/p/css03/esgf_publish/cmip3/ipcc/cfmip/2xco2/atm/da/pr/ukmo_hadsm4/run1": [
        "pr_CF3.nc",
        "bad time dimension",
        "",
        [],
    ],
    "/p/css03/esgf_publish/cmip3/ipcc/cmip5/ozone/": [
        "",
        "",
        [],
    ],  # CMIP5 ozone forcing data
    # "/p/css03/esgf_publish/cmip3/ipcc/20c3m/atm/da/rlus/miub_echo_g/run1": ["rlus_A2_a42_0108-0147.nc", "bad time dimension values", "", []],
    # /p/css03/esgf_publish/cmip3/ipcc/cfmip/2xco2/atm/mo/rsut/mpi_echam5/run1/rsut_CF1.nc
}
excludeDirs = set(["summer", "cam3.3", "T4031qt"])
excludeDirs2 = set(["ipcc"])
# 004306 filePath: /p/css03/esgf_publish/cmip3/ipcc/summer/T4031qtC.pop.h.0019-08-21-43200.nc

# %% iterate over files
cm3 = {}
cm3["!badFile"] = {}
cm3["!noDateFile"] = {}
cm3["!fileReadError"] = {}
badFileCount, cmorCount, count, fileReadErrorCount, noDateFileCount = [
    0 for _ in range(5)
]
for cmPath in [
    "/p/css03/esgf_publish/cmip3",
    "/p/css03/scratch/ipcc2_deleteme_July2020",
]:
    # for cmPath in ["/p/css03/esgf_publish/cmip3/ipcc/20c3m/atm/da/rlus/miub_echo_g/run1"]:  # bug hunting
    # for cmPath in list(bad.keys()):
    for root, dirs, files in os.walk(cmPath):
        print("root:", root)
        # Add dirs to exclude;
        [dirs.remove(d) for d in list(dirs) if d in excludeDirs]
        if root.split("/")[-1] == "ipcc":
            [dirs.remove(d) for d in list(dirs) if d in excludeDirs2]  # catch ipcc/ipcc
        if root in list(bad.keys()):
            # Weed out bad paths/files
            # print("in here!")
            # pdb.set_trace()
            badFile = bad[root][0]
            fixStrInfo = bad[root][1]
            fixStr = bad[root][2]
            if bad[root][3] != []:
                badVars = bad[root][3][0]
            else:
                badVars = None
        else:
            badFile, fixStrInfo, fixStr, badVars = [None for _ in range(4)]
            # continue
        if files:
            # print("files:", files)
            files.sort()  # sort to process sequentially
            for c1, fileName in enumerate(files):
                filePath = os.path.join(root, fileName)
                print("{:06d}".format(count), "filePath:", filePath)
                # get sha256
                sha256 = getSha256(filePath)
                # get fileSizeBytes, fileModTime
                fileSizeBytes, fileModTime = getFileStats(filePath)
                if filePath[-3:] != ".nc":  # deal with *.nc.bad files
                    badFileCount = badFileCount + 1
                    print("no date; filePath:", filePath)
                    cm3["!badFileCount"] = badFileCount
                    cm3["!badFile"][badFileCount] = filePath
                elif filePath[-3:] == ".nc":  # process all "good" files
                    if c1 == 0:
                        cm3[root] = {}  # create dir entry for each file
                    elif root not in cm3.keys():
                        # create dir entry for each file, if first file bad
                        cm3[root] = {}
                    cmorVersion, dateFound = [
                        False for _ in range(2)
                    ]  # set for each file
                    count = count + 1  # file counter
                    # open and deal with file issues
                    # pdb.set_trace()
                    try:
                        # wrap so bombs are caught in except
                        if fixStr == None and badVars == None and badFile == None:
                            fh = open_dataset(filePath, use_cftime=True)
                        # Case bad root match, but not file
                        elif fixStrInfo and (badFile != fileName and not badFile == ""):
                            fh = open_dataset(filePath, use_cftime=True)
                        # Case bad root match, AND file
                        elif badVars and (fileName == badFile):  # badVars only
                            print("badVars:", badVars)
                            fh = xr.open_dataset(
                                filePath, drop_variables=[badVars]
                            ).pipe(xr.decode_cf)
                        elif badFile == "":  # fixFunc for all files only - 9863
                            print("badFile == ''")
                            fh = (
                                xr.open_dataset(filePath, decode_times=False)
                                .pipe(fixFunc(fixStr, fixStrInfo))
                                .pipe(xr.decode_cf)
                            )
                        # is there a need for fixFunc AND badVars?
                        elif badVars == [] and (fileName == badFile):
                            # print("elif3")
                            # pdb.set_trace()
                            badFileCount = badFileCount + 1
                            print("badFile; filePath:", filePath)
                            cm3["!badFileCount"] = badFileCount
                            cm3["!badFile"][badFileCount] = filePath
                            continue
                    except Exception as ex:
                        print("except", ex)
                        # pdb.set_trace()
                        fileReadErrorCount = fileReadErrorCount + 1
                        print("fileReadError; filePath:", filePath)
                        cm3["!fileReadErrorCount"] = fileReadErrorCount
                        cm3["!fileReadError"][fileReadErrorCount] = filePath
                        continue
                    if "T" in fh.cf.axes:
                        startTime = getTimes(fh.time[0])
                        endTime = getTimes(fh.time[-1])
                    else:
                        startTime, endTime = [None for _ in range(2)]
                    attDict = fh.attrs

                    # impose filesystem file modification date
                    date = fileModTime
                    dateFoundAtt = "os.stat().st_mtime"

                    # work through all attributes to seek and overwrite date string
                    for att in attList:
                        if att not in attDict.keys():
                            # print(att, "not in file, skipping..")
                            continue
                        if isinstance(attDict[att], str):
                            print("att:", att)
                            attStr = attDict[att]
                            # print("attStr:", attStr)
                            # BCCR_BCM2_0 format
                            if att == "date":
                                date = attStr
                                date = date.split("-")
                                day = date[0]
                                mon = "{:02d}".format(monList.index(date[1]) + 1)
                                yr = date[-1]
                                date = makeDate(yr, mon, day, check=True)
                                dateFound = True
                                dateFoundAtt = att
                            # Deal with CMOR matches
                            if "CMOR rewrote data to comply" in attStr:
                                attStrInd = attStr.index(" At ")
                                attStr = attStr[attStrInd:]
                                date = re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}", attStr)
                                date = date[0].split("/")
                                # assuming mm/dd/yyyy e.g. At 20:53:22 on 06/28/2005, CMOR rewrote data to comply with CF standards and IPCC Fourth Assessment requirements
                                date = makeDate(date[-1], date[0], date[1], check=True)
                                cmorCount = cmorCount + 1
                                if "cmor_version" in fh.attrs.keys():
                                    cmorVersion = fh.attrs["cmor_version"]
                                dateFound = True
                                dateFoundAtt = att
                            # Deal with regex matches
                            dateReg = [
                                r"[0-3][0-9]/[0-3][0-9]/(?:[0-9][0-9])?[0-9][0-9]",
                                r"year:[0-9]{4}:month:[0-9]{2}:day:[0-9]{2}",
                                # r"Fri Aug  5 19:23:54 MDT 2005"
                                r"[a-zA-Z]{3}\s[a-zA-Z]{3}\s{1,2}\d{1,2}\s\d{1,2}.\d{2}.\d{2}\s[A-Z]{3}\s\d{4}",
                            ]
                            for dateFormat in dateReg:
                                if dateFound:
                                    continue
                                date = re.findall(dateFormat, attStr)
                                # timezones")
                                timeZones = ["EDT", "EST", "MDT", "MST", "PDT", "PST"]
                                # CSIRO format - r"year:[0-9]{4}:month:[0-9]{2}:day:[0-9]{2}"
                                if date and ("year" in date[0]):
                                    date = (
                                        date[0]
                                        .replace("year:", "")
                                        .replace(":month:", "-")
                                        .replace(":day:", "-")
                                    )
                                    dateFound = True
                                    dateFoundAtt = att
                                # NCAR CCSM format - r"[a-zA-Z]{3}\s[a-zA-Z]{3}\s{1,2}\d{1,2}\s\d{1,2}.\d{2}.\d{2}\s[A-Z]{3}\s\d{4}"
                                elif date and any(
                                    zone in date[0] for zone in timeZones
                                ):
                                    date = date[0].split(" ")
                                    mon = "{:02d}".format(monList.index(date[1]) + 1)
                                    yr = date[-1]
                                    if len(date) == 6:
                                        day = date[2]
                                    elif len(date) == 7:
                                        day = date[3]
                                    day = "{:02d}".format(int(day))
                                    date = makeDate(yr, mon, day, check=True)
                                    dateFound = True
                                    dateFoundAtt = att
                    # if a valid date start saving pieces
                    if date:
                        # save filePath, fileName, attName, date
                        cm3[root][fileName] = {}
                        cm3[root][fileName]["date"] = [date, dateFoundAtt]
                        cm3[root][fileName]["time0"] = startTime
                        cm3[root][fileName]["timeN"] = endTime
                        cm3[root][fileName]["sha256"] = sha256
                        cm3[root][fileName]["filePath"] = filePath
                        cm3[root][fileName]["fileSizeBytes"] = fileSizeBytes
                        if cmorVersion:
                            cm3[root][fileName]["cmorVersion"] = str(cmorVersion)
                        cm3["!_cmorCount"] = cmorCount
                        cm3["!_fileCount"] = count  # https://ascii.cl/
                    if not date:
                        pdb.set_trace()
                        # noDateFileCount = noDateFileCount+1
                        # print("no date; filePath:", filePath)
                        # cm3["!noDateFileCount"] = noDateFileCount
                        # cm3["!noDateFile"][noDateFileCount] = [
                        #    filePath, sha256, fileSizeBytes]
                    print("date:", date)

                    # close open file
                    fh.close()

        # save dictionary ## if files
        timeNow = datetime.datetime.now()
        timeFormatDir = timeNow.strftime("%y%m%d")
        outFile = "_".join([timeFormatDir, "cmip3.json"])
        if os.path.exists(outFile):
            os.remove(outFile)
        print("writing:", outFile)
        fH = open(outFile, "w")
        json.dump(
            cm3,
            fH,
            ensure_ascii=True,
            sort_keys=True,
            indent=4,
            separators=(",", ":"),
        )
        fH.close()

"""
067561 filePath: /p/css03/esgf_publish/cmip3/ipcc/20c3m/atm/da/rlus/miub_echo_g/run1/rlus_A2_a42_0108-0147.nc
Traceback (most recent call last):
  File "/p/user_pub/climate_work/durack1/tmp/scanCMIP3.py", line 220, in <module>
    fh = open_dataset(filePath, use_cftime=True)
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xcdat/dataset.py", line 105, in open_dataset
    ds = xr.open_dataset(path, decode_times=True, **kwargs)  # type: ignore
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/backends/api.py", line 531, in open_dataset
    backend_ds = backend.open_dataset(
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/backends/netCDF4_.py", line 569, in open_dataset
    ds = store_entrypoint.open_dataset(
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/backends/store.py", line 41, in open_dataset
    ds = Dataset(vars, attrs=attrs)
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/core/dataset.py", line 599, in __init__
    variables, coord_names, dims, indexes, _ = merge_data_and_coords(
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/core/merge.py", line 575, in merge_data_and_coords
    return merge_core(
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/core/merge.py", line 755, in merge_core
    collected = collect_variables_and_indexes(aligned, indexes=indexes)
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/core/merge.py", line 365, in collect_variables_and_indexes
    variable = as_variable(variable, name=name)
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/core/variable.py", line 167, in as_variable
    obj = obj.to_index_variable()
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/core/variable.py", line 543, in to_index_variable
    return IndexVariable(
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/core/variable.py", line 2724, in __init__
    self._data = PandasIndexingAdapter(self._data)
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/core/indexing.py", line 1418, in __init__
    self.array = safe_cast_to_index(array)
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/core/utils.py", line 139, in safe_cast_to_index
    index = pd.Index(np.asarray(array), **kwargs)
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/core/indexing.py", line 524, in __array__
    return np.asarray(array[self.key], dtype=None)
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/coding/variables.py", line 72, in __array__
    return self.func(self.array)
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/coding/times.py", line 293, in decode_cf_datetime
    dates = _decode_datetime_with_cftime(flat_num_dates, units, calendar)
  File "/home/durack1/mambaforge/envs/xcd031spy532mat353/lib/python3.10/site-packages/xarray/coding/times.py", line 201, in _decode_datetime_with_cftime
    cftime.num2date(num_dates, units, calendar, only_use_cftime_datetimes=True)
  File "src/cftime/_cftime.pyx", line 586, in cftime._cftime.num2date
  File "src/cftime/_cftime.pyx", line 385, in cftime._cftime.cast_to_int
OverflowError: time values outside range of 64 bit signed integers

"""
