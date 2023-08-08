#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 7 14:27:34 2023

PJD  7 Aug 2023     - Written to collect functions being used across libraries

@author: durack1
"""

# %% imports
import datetime
import hashlib
import json
import os

# import pdb

# %% function defs


def checkDate(dateStr):
    # assume 2022-10-05 format
    y, m, d = dateStr.split("-")
    # test month
    if not 1 <= int(m) <= 12:
        print("month invalid:", m)
        return None
    # test day
    if not 1 <= int(d) <= 31:
        print("day invalid:", d)
        return None
    # test year
    if not 2003 <= int(y) <= 2008:
        print("year invalid:", y)
        return None  # dateStr  # return even if invalid, was None

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
            fileModTime.year, fileModTime.month, fileModTime.day, False
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
    # experiments = {"pdcntrl", "picntrl", "20c3m", "sresa1b", "sresa2", "sresb1"}
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


def setTimes(fh):
    if "T" in fh.cf.axes:
        startTime = getTimes(fh.time[0])
        endTime = getTimes(fh.time[-1])
    else:
        startTime, endTime = [None for _ in range(2)]

    return startTime, endTime


def writeJson(dictToWrite, fileText, timeFormatDir=""):
    # save dictionary
    if timeFormatDir == "":
        timeNow = datetime.datetime.now()
        timeFormatDir = timeNow.strftime("%y%m%d")
    outFile = ".".join(["_".join([timeFormatDir, fileText]), "json"])
    if os.path.exists(outFile):
        os.remove(outFile)
    print("writing:", outFile)
    fH = open(outFile, "w")
    json.dump(
        dictToWrite,
        fH,
        ensure_ascii=True,
        sort_keys=True,
        indent=4,
        separators=(",", ":"),
    )
    fH.close()
