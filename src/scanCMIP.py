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
PJD 16 Apr 2024     - Update to attempt CMIP5/6 scanning
PJD 18 Apr 2024     - Update for CMIP5/6 scanning; pull cmor_version check up
PJD 18 Apr 2024     - Renamed scanCMIP3 -> scanCMIP.py
PJD 20 Aug 2024     - Added strCounter to separate files to 100000 entries - stop GB write slowdown
PJD 21 Aug 2024     - Updated to delete cm dictionary and rebuild, solving file growth problem
PJD 22 Aug 2024     - Added dirCount logic
                    TODO: add time start/stop to fileNames that exclude them
                    TODO: table mappings O1 = Omon?, O1e?

@author: durack1
"""

import argparse
import datetime
import hashlib
import json
import os
import pdb
import re
import xarray as xr
from xcdat import open_dataset

# import pdb
# import shutil
# import sys
# import time

# %% assign which CMIP phase you are targeting - set years and paths
cmDict = {}
cmDict["CMIP3"] = {}
cmDict["CMIP3"]["startYr"] = 2003
cmDict["CMIP3"]["endYr"] = 2008
cmDict["CMIP3"]["paths"] = [
    "/p/css03/esgf_publish/cmip3",
    "/p/css03/scratch/ipcc2_deleteme_July2020",
]
cmDict["CMIP5"] = {}
cmDict["CMIP5"]["startYr"] = 2008
cmDict["CMIP5"]["endYr"] = 2017
cmDict["CMIP5"]["paths"] = [
    "/p/css03/cmip5_css01/data/cmip5/output1",
    "/p/css03/cmip5_css02/data/cmip5/output1",
    "/p/css03/cmip5_css02/data/cmip5/output2",
    "/p/css03/esgf_publish/cmip5",
]
cmDict["CMIP6"] = {}
cmDict["CMIP6"]["startYr"] = 2018
cmDict["CMIP6"]["endYr"] = 2026
cmDict["CMIP6"]["paths"] = [
    "/p/css03/esgf_publish/CMIP6",
    "/p/css03/scratch/CMIP6/",
]

# add runtime argument
parser = argparse.ArgumentParser(description="Obtain CMIP era being scanned")
parser.add_argument(
    "-e",
    "--era",
    help="Integer indicating CMIP era",
    required=True,
    choices=["3", "5", "6"],
)
args = vars(parser.parse_args())
era = "".join(["CMIP", args["era"]])
startYr = cmDict[era]["startYr"]
endYr = cmDict[era]["endYr"]
paths = cmDict[era]["paths"]
print(era, startYr, endYr)

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


def checkDate(dateStr, startYr, endYr):
    # assume 2022-10-05 format
    y, m, d = dateStr.split("-")
    if not startYr <= int(y) <= endYr:
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


def getFileSize(filePath):
    if os.path.isfile(filePath):
        fileStats = os.stat(filePath)
        fileSizeBytes = fileStats.st_size
    else:
        print("File:", filePath, "not a valid file")
        fileSizeBytes = 0.0

    return fileSizeBytes


def getSha256(filePath, print=False):
    with open(filePath, "rb") as f:
        bytes = f.read()  # read entire file as bytes
        readable_hash = hashlib.sha256(bytes).hexdigest()
        if print:
            print(readable_hash)

    return readable_hash


def getTimes(time, startYr, endYr):
    y = int(time.dt.year.data)
    m = int(time.dt.month.data)
    d = int(time.dt.day.data)
    dateStr = makeDate(y, m, d, startYr, endYr, check=False)

    return dateStr


def makeDate(year, month, day, startYr, endYr, check):
    date = "-".join([str(year), str(month), str(day)])
    # print("makeDate: date =", date)
    # pdb.set_trace()
    if check:
        date = checkDate(date, startYr, endYr)

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
            cm["!badFileCount"] = badFileCount
            cm["!badFileList"][badFileCount] = filePath
            continue
    except:
        fileReadErrorCount = fileReadErrorCount+1
        print("fileReadError; filePath:", filePath)
        cm["!fileReadErrorCount"] = fileReadErrorCount
        cm["!fileReadError"][fileReadErrorCount] = filePath
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
    "creation_date",  # CMIP6 NCAR CESM2
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
    # "/p/css03/esgf_publish/cmip3/ipcc/20c3m/atm/da/rlus/miub_echo_g/run1": ["rlus_A2_a42_0108-0147.nc", "bad time dimension values", "", []],
    # /p/css03/esgf_publish/cmip3/ipcc/cfmip/2xco2/atm/mo/rsut/mpi_echam5/run1/rsut_CF1.nc
}
excludeDirs = set(["summer", "cam3.3", "T4031qt"])
excludeDirs2 = set(["ipcc"])
# 004306 filePath: /p/css03/esgf_publish/cmip3/ipcc/summer/T4031qtC.pop.h.0019-08-21-43200.nc

# %% iterate over files
cm = {}
cm["!badFile"] = {}
cm["!noDateFile"] = {}
cm["!fileReadError"] = {}
(
    badFileCount,
    cmorCount,
    count,
    dirCount,
    fileReadErrorCount,
    noDateFileCount,
    strCounter,
) = [0 for _ in range(7)]
for cmPath in paths:
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
                # get fileSizeBytes
                fileSizeBytes = getFileSize(filePath)
                if filePath[-3:] != ".nc":  # deal with *.nc.bad files
                    badFileCount = badFileCount + 1
                    print("no date; filePath:", filePath)
                    cm["!badFileCount"] = badFileCount
                    cm["!badFile"][badFileCount] = filePath
                elif filePath[-3:] == ".nc":  # process all "good" files
                    if c1 == 0:
                        cm[root] = {}  # create dir entry for each file
                    elif root not in cm.keys():
                        # create dir entry for each file, if first file bad
                        cm[root] = {}
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
                            cm["!badFileCount"] = badFileCount
                            cm["!badFile"][badFileCount] = filePath
                            continue
                    except:
                        print("except")
                        # pdb.set_trace()
                        fileReadErrorCount = fileReadErrorCount + 1
                        print("fileReadError; filePath:", filePath)
                        cm["!fileReadErrorCount"] = fileReadErrorCount
                        cm["!fileReadError"][fileReadErrorCount] = filePath
                        continue
                    if "T" in fh.cf.axes:
                        startTime = getTimes(fh.time[0], startYr, endYr)
                        endTime = getTimes(fh.time[-1], startYr, endYr)
                    else:
                        startTime, endTime = [None for _ in range(2)]
                    attDict = fh.attrs
                    for att in attList:
                        if not att in attDict.keys():
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
                                date = makeDate(
                                    yr, mon, day, startYr, endYr, check=True
                                )
                                dateFound = True
                                dateFoundAtt = att
                            # Deal with CMOR matches
                            if "CMOR rewrote data to comply" in attStr:
                                if era == "CMIP3":  # CMOR1
                                    # assuming mm/dd/yyyy e.g. At 20:53:22 on 06/28/2005, CMOR rewrote data to comply with CF standards and IPCC Fourth Assessment requirements
                                    attStrInd = attStr.index(" At ")
                                    attStr = attStr[attStrInd:]
                                    date = re.findall(
                                        r"\d{1,2}/\d{1,2}/\d{2,4}", attStr
                                    )
                                    date = date[0].split("/")
                                    date = makeDate(
                                        date[-1],
                                        date[0],
                                        date[1],
                                        startYr,
                                        endYr,
                                        check=True,
                                    )
                                elif era == "CMIP5":  # CMOR2
                                    # assuming YYYY-MM-DDTHH:MM:SSZ e.g. ..from cfsv2_decadal runs. 2013-03-12T17:53:48Z CMOR rewrote data to comply with CF standards and CMIP5 requirements.
                                    attStrInd = attStr.index(
                                        "Z CMOR rewrote data to comply"
                                    )
                                    attStr = attStr[attStrInd - 19 : attStrInd]
                                    date = re.findall(
                                        r"\d{1,4}-\d{1,2}-\d{1,2}", attStr
                                    )
                                    date = date[0].split("-")
                                    date = makeDate(
                                        date[0],
                                        date[1],
                                        date[2],
                                        startYr,
                                        endYr,
                                        check=True,
                                    )
                                elif era == "CMIP6":
                                    # assuming ??? CMOR3
                                    attStrInd = attStr.index(
                                        "Z CMOR rewrote data to comply"
                                    )
                                    attStr = attStr[attStrInd - 19 : attStrInd]
                                    date = re.findall(
                                        r"\d{1,4}-\d{1,2}-\d{1,2}", attStr
                                    )
                                    date = date[0].split("-")
                                    date = makeDate(
                                        date[0],
                                        date[1],
                                        date[2],
                                        startYr,
                                        endYr,
                                        check=True,
                                    )
                                # Proceed with globalAtts
                                # dateFound = True
                                dateFoundAtt = att
                            # Deal with regex matches
                            dateReg = [
                                r"[0-3][0-9]/[0-3][0-9]/(?:[0-9][0-9])?[0-9][0-9]",
                                r"year:[0-9]{4}:month:[0-9]{2}:day:[0-9]{2}",
                                # r"Fri Aug  5 19:23:54 MDT 2005"
                                r"[a-zA-Z]{3}\s[a-zA-Z]{3}\s{1,2}\d{1,2}\s\d{1,2}.\d{2}.\d{2}\s[A-Z]{3}\s\d{4}",
                                # :creation_date = "2021-05-06T18:58:51Z" CMIP6/ISMIP6/NCAR/CESM2/ssp585-withism/r1i1p1f1/ImonGre/rlds/gn/v20210513
                                r"\d{1,4}-\d{1,2}-\d{1,2}T\d{1,2}:\d{1,2}:\d{1,2}Z",
                            ]
                            # check if dateFound, otherwise drop into other attributes for matches
                            if dateFound:
                                continue
                            # start checking other attributes
                            for dateFormat in dateReg:
                                # print("for dateFormat:", dateFormat)
                                # print("dateFound:", dateFound)
                                # pdb.set_trace()
                                date = re.findall(dateFormat, attStr)
                                # print("re.date:", date)
                                # timezones
                                timeZones = [
                                    "EDT",
                                    "EST",
                                    "MDT",
                                    "MST",
                                    "PDT",
                                    "PST",
                                ]
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
                                # CMIP3 NCAR CCSM format - r"[a-zA-Z]{3}\s[a-zA-Z]{3}\s{1,2}\d{1,2}\s\d{1,2}.\d{2}.\d{2}\s[A-Z]{3}\s\d{4}"
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
                                    date = makeDate(
                                        yr, mon, day, startYr, endYr, check=True
                                    )
                                    dateFound = True
                                    dateFoundAtt = att
                                # CMIP6 NCAR CESM2 format r"\d{1,4}-\d{1,2}-\d{1,2}T\d{1,2}:\d{1,2}:\d{1,2}Z"
                                if date and re.match(
                                    r"\d{1,4}-\d{1,2}-\d{1,2}T\d{1,2}:\d{1,2}:\d{1,2}Z",
                                    date[0],
                                ):
                                    date = date[0].split("T")
                                    # print(date)
                                    date = date[0].split("-")
                                    yr = date[0]
                                    mon = date[1]
                                    day = date[2]
                                    date = makeDate(
                                        yr, mon, day, startYr, endYr, check=True
                                    )
                                    dateFound = True
                                    dateFoundAtt = att
                    # cmor_version?
                    if "cmor_version" in fh.attrs.keys():
                        cmorVersion = fh.attrs["cmor_version"]
                        cmorCount = cmorCount + 1
                    # if a valid date start saving pieces
                    if date:
                        # save filePath, fileName, attName, date
                        cm[root][fileName] = {}
                        cm[root][fileName]["date"] = [date, dateFoundAtt]
                        cm[root][fileName]["time0"] = startTime
                        cm[root][fileName]["timeN"] = endTime
                        cm[root][fileName]["sha256"] = sha256
                        cm[root][fileName]["filePath"] = filePath
                        cm[root][fileName]["fileSizeBytes"] = fileSizeBytes
                        if cmorVersion:
                            cm[root][fileName]["cmorVersion"] = str(cmorVersion)
                        cm["!_cmorCount"] = cmorCount
                        cm["!_fileCount"] = count  # https://ascii.cl/
                    if not date:
                        noDateFileCount = noDateFileCount + 1
                        print("no date; filePath:", filePath)
                        cm["!noDateFileCount"] = noDateFileCount
                        cm["!noDateFile"][noDateFileCount] = [
                            filePath,
                            sha256,
                            fileSizeBytes,
                        ]
                    print("date:", date)

                    # close open file
                    fh.close()

                # if filePath[-3:] != ".nc":

            # save dictionary ## if files and completed dir
            dirCount = dirCount + 1  # directory counter
            # timeNow = datetime.datetime.now()
            # timeFormatDir = timeNow.strftime("%y%m%d")
            # outFile = "_".join([timeFormatDir, ".".join([era, "json"])])
            outFile = "_".join([era, ".".join(["{:03d}".format(strCounter), "json"])])
            if os.path.exists(outFile):
                os.remove(outFile)
            print("writing:", outFile)
            fH = open(outFile, "w")
            json.dump(
                cm,
                fH,
                ensure_ascii=True,
                sort_keys=True,
                indent=4,
                separators=(",", ":"),
            )
            fH.close()

            # create filename dynamically from dirCount
            countLim = 10
            if not dirCount % countLim and (dirCount != 0):  # if true will execute
                print("dirCount/countLim:", dirCount, (dirCount % countLim))
                pdb.set_trace()
                strCounter = int(dirCount / countLim)
                # create new dictionary
                # dict_keys(['!_cmorCount', '!_fileCount', '!badFile', '!fileReadError', '!noDateFile',
                cmorCountTmp = cm["!_cmorCount"]
                fileCountTmp = cm["!_fileCount"]
                badFileTmp = cm["!badFile"]
                fileReadErrorTmp = cm["!fileReadError"]
                noDateFileTmp = cm["!noDateFile"]
                cm = {}
                cm["!_cmorCount"] = cmorCountTmp
                cm["!_fileCount"] = fileCountTmp
                cm["!badFile"] = badFileTmp
                cm["!fileReadError"] = fileReadErrorTmp
                cm["!noDateFile"] = noDateFileTmp
