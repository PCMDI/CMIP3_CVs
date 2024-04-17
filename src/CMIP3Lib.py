#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 7 14:27:34 2023

PJD  7 Aug 2023     - Written to collect functions being used across libraries
PJD  9 Aug 2023     - Added makeDRS.py functions

@author: durack1
"""

# %% imports
import datetime
import hashlib
import json
import os
import pdb
import re

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


def fixSource(sourceId):
    # switch case
    sourceId = sourceId.upper()
    sourceId = sourceId.replace("HAD", "Had")  # fix Had
    sourceId = sourceId.replace("MK3", "Mk3")  # fix Mk3
    sourceId = sourceId.replace("CCCMA", "CCCma")  # fix CCCMA
    # switch underscores
    sourceId = sourceId.replace("_", "-")

    return sourceId


def formatDate(dateStr):
    # assume 2023-7-26
    y, m, d = dateStr.split("-")
    # generate 20230726
    dateStr = "".join(
        ["{:04}".format(int(y)), "{:02}".format(int(m)), "{:02}".format(int(d))]
    )

    return dateStr


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


def matchExperiment(pathBits):
    # define exps
    experiments = [
        "1pctto2x",
        "1pctto4x",
        "20c3m",
        "2xco2",
        "amip",
        "commit",
        "pdcntrl",
        "picntrl",
        "slabcntl",
        "sresa1b",
        "sresa2",
        "sresb1",
    ]
    cfmip = ["2xco2", "slabcntl"]
    scenariomip = ["sresa1b", "sresa2", "sresb1"]
    expId = [el for el in pathBits if el in experiments]
    if not len(expId):
        pdb.set_trace()
    if expId in cfmip:
        actId = "CFMIP"
    elif expId in scenariomip:
        actId = "ScenarioMIP"
    else:
        actId = "CMIP"

    return expId, actId


def matchFrequency(pathBits):
    frequencies = ["3h", "da", "fixed", "mo", "yr"]
    freqId = [el for el in pathBits if el in frequencies]
    if not len(freqId):
        pdb.set_trace()
    # get var, src_id
    freqInd = pathBits.index(freqId[0])
    varId = pathBits[freqInd + 1]
    srcId = pathBits[freqInd + 2]

    return freqId, varId, srcId


def matchInst(srcId):
    # see details at https://pcmdi.llnl.gov/ipcc/model_documentation/ipcc_model_documentation.html
    # and also https://www.ipcc-data.org/auto/ar4/
    if srcId == "BCC-CM1":
        instId = "BCC"  # retracted immediately after submission
    elif srcId == "BCCR-BCM2-0":
        instId = "NCC"
        # " BCCR (Bjerknes Centre for Climate Research)\n",
        # " University of Bergen, Norway (www.bjerknes.uib.no)\n",
        # " NERSC (Nansen Environmental and Remote Sensing Center, Norway (www.nersc.no)\n",
        # " GFI (Geophysical Institute) University of Bergen, Norway (www.gfi.uib.no)" ;
    elif srcId == "BMRC1":
        instId = "BMRC"  # (Aust) Bureau of Meteorology Research Centre
    elif srcId in ["CCCma-AGCM4-0", "CCCma-CGCM3-1", "CCCma-CGCM3-1-T63"]:
        instId = "CCCma"
    elif srcId == "CNRM-CM3":
        instId = "CNRM-CERFACS"
    elif srcId in ["CSIRO-Mk3-0", "CSIRO-Mk3-5"]:
        instId = "CSIRO"
    elif srcId in ["GFDL-CM2-0", "GFDL-CM2-1", "GFDL-MLM2-1"]:
        instId = "NOAA-GFDL"
    elif srcId in ["GISS-AOM", "GISS-MODEL-E-H", "GISS-MODEL-E-R"]:
        instId = "NASA-GISS"
    elif srcId == "IAP-FGOALS1-0-G":
        instId = "CAS"
        # IAP - Institute of Atmospheric Physics, Chinese Academy of Sciences
    elif srcId == "INGV-ECHAM4":
        instId = "CMCC"
        # Istituto Nazionale di Geofisica e Vulcanologia (INGV) and
        # Numerical Applications and Scenarios Division, CMCC
        # https://www.cmcc.it/wp-content/uploads/2012/08/rp0015-ans-02-2007-1.pdf
    elif srcId == "INMCM3-0":
        instId = "INM"
    elif srcId == "IPSL-CM4":
        instId = "IPSL"
    elif srcId in ["MIROC-HISENS", "MIROC-LOSENS", "MIROC3-2-HIRES", "MIROC3-2-MEDRES"]:
        instId = "MIROC"
    elif srcId == "MIUB-ECHO-G":
        instId = "MIUB"
        # Meteorological Institute of the University of Bonn (MIUB)
    elif srcId == "MPI-ECHAM5":
        instId = "MPI-M"
    elif srcId == "MRI-CGCM2-3-2A":
        instId = "MRI"
    elif srcId in ["NCAR-CCSM3-0", "NCAR-PCM1"]:
        instId = "NCAR"
    elif srcId == "UIUC":
        instId = "UIUC"
        # University of Illinois at Urbana-Champaign - CFMIP contributor
    elif srcId in [
        "UKMO-HadCM3",
        "UKMO-HadGEM1",
        "UKMO-HadGSM1",
        "UKMO-HadSM3",
        "UKMO-HadSM4",
    ]:
        instId = "MOHC"
    else:
        instId = None

    return instId


def matchRealm(pathBits):
    realms = ["atm", "ice", "land", "ocn"]
    realm = [el for el in pathBits if el in realms]
    if not len(realm):
        pdb.set_trace()

    return realm


def matchRun(pathBits):
    r = re.compile(r"run[0-9]")
    run = list(filter(r.match, pathBits))
    if not len(run):
        pdb.set_trace()

    return run


def matchTable(fileName):
    tables = [
        "A1",  # https://github.com/PCMDI/cmip3-cmor-tables
        "A1A",
        "A1B",
        "A1C",
        "A1D",
        "A1E",
        "A1F",
        "A2",
        "A2A",
        "A2B",
        "A3",
        "A4",
        "A5",
        "O1",
        "O1A",
        "O1B",
        "O1C",
        "O1D",
        "O1E",
        "O1F",
        "O1G",
        "CF1",  # https://github.com/PCMDI/cfmip1-cmor-tables
        "CF1A",
        "CF1B",
        "CF1C",
        "CF1D",
        "CF1E",
        "CF2",
        "CF2A",
        "CF2B",
        "CF3",
        "CF3A",
        "CF3B",
        "CF3C",
        "CF3D",
        "CF4",
    ]
    # first merge multiple files
    fileName = "".join(fileName)
    # split "_"
    fileBits = [x.upper() for x in fileName.split("_")]
    print("fileBits1:", fileBits)
    # split "."
    fileBits = [item.split(".") for item in fileBits]
    print("fileBits2:", fileBits)
    # flatten
    fileBits = [el for innerList in fileBits for el in innerList]
    print("fileBits3:", fileBits)
    tableId = [el for el in fileBits if el in tables]

    if not len(tableId):
        print("not len(tableId):", tableId)
        pdb.set_trace()

    return tableId[0]


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
