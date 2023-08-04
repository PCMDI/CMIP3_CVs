#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 15:14:34 2023

PJD 24 Jul 2023     - Written to organize CMIP3 data using CMIP6 DRS

Plans
1. Process all valid keys
2. Process all !noDateFile entries (using similar inst/mod/exp/table contributions)
3. Process all !fileReadError entries (is there an xarray pipe that fixes it)
4. Process/archive all !badFile entries (along with BCC-CM1, which was unpublished? - Karl)

@author: durack1
"""

# %% imports
import json
import os
import pdb
import re

# import time

# %% function defs


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
        instId = (
            "CAS"  # IAP - Institute of Atmospheric Physics, Chinese Academy of Sciences
        )
    elif srcId == "INGV-ECHAM4":
        instId = "CMCC"
        # Istituto Nazionale di Geofisica e Vulcanologia ((INGV) and
        # Numerical Applications and Scenarios Division, CMCC
        # https://www.cmcc.it/wp-content/uploads/2012/08/rp0015-ans-02-2007-1.pdf
    elif srcId == "INMCM3-0":
        instId = "INM"
    elif srcId == "IPSL-CM4":
        instId = "IPSL"
    elif srcId in ["MIROC-HISENS", "MIROC-LOSENS", "MIROC3-2-HIRES", "MIROC3-2-MEDRES"]:
        instId = "MIROC"
    elif srcId == "MIUB-ECHO-G":
        instId = "MIUB"  # Meteorological Institute of the University of Bonn (MIUB)
    elif srcId == "MPI-ECHAM5":
        instId = "MPI-M"
    elif srcId == "MRI-CGCM2-3-2A":
        instId = "MRI"
    elif srcId in ["NCAR-CCSM3-0", "NCAR-PCM1"]:
        instId = "NCAR"
    elif srcId == "UIUC":
        instId = (
            "UIUC"  # University of Illinois at Urbana-Champaign - CFMIP contributor
        )
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


# %% load data
infile = "230723_cmip3.json"
filePath = "/home/durack1/git/CMIP3_CVs/src"
infilePath = os.path.join(filePath, infile)

with open(infilePath) as fH:
    a = json.load(fH)

del fH

# %% create exclusion keys
badKeys = [
    "!_cmorCount",
    "!_fileCount",
    "!badFile",
    "!badFileCount",
    "!fileReadError",
    "!fileReadErrorCount",
    "!noDateFile",
    "!noDateFileCount",
]

# %% start interrogating dictionary
dirList = list(a.keys())
print("len(dirList):", len(dirList))
print("len(badKeys):", len(badKeys))
for key in badKeys:
    dirList.remove(key)
print("len(dirList):", len(dirList))

# %% determine unique files - use sha256 as handles
sha256s = []
for i, d in enumerate(dirList):
    files = a[d]
    for file in files:
        sha256 = a[d][file]["sha256"]
        # print(i, sha256, file, files[file]["filePath"])
        sha256s.append(sha256)

"""
# determine duplicates (deprecated)
# seen = set()
# dupes = [x for x in sha256s if x in seen or seen.add(x)]
# print("len(dupes):", len(dupes))
# dupes = set(dupes)
# print("len(set(dupes)):", len(dupes))
# report dupe count
# print(
#    "len(dupes):",
#    len(dupes),
#    "; len(sha256s):",
#    len(sha256s),
#    "; dupe%:",
#    "{:3.1f}".format((len(dupes) / len(sha256s)) * 100),
# )
"""

sha256uniq = set(sha256s)
sha256uniqL = list(sha256uniq)
sha256uniqL.sort()  # create persistently ordered list
# sets are inconsistent

emptyDir = []
filesToProcess = []
dupeDict = {}
for i, sha in enumerate(sha256uniqL):  # 28499 trigger test
    print("----------")
    print("{:06}".format(i), sha)
    count = 0
    shaMatch = []
    # loop through all valid directories
    for d in dirList:
        # for each directory determine files
        files = a[d]
        if len(files) == 0:
            if d not in emptyDir:
                emptyDir.append(d)
                print("emptyDir:", len(emptyDir), d)
                # pdb.set_trace()  # time.sleep(2)
                continue
        # else if files exist, interrogate
        else:
            # loop through files - match with sha
            for file in files:
                if files[file]["sha256"] == sha:
                    shaMatch.append(["file:", file, d])
                    count += 1
    # if no matches, add single file, path
    if count == 1:
        filesToProcess.append([file, d])
    # if no matches, add single file, path
    # using min dir/len to weed out *dataX*, *deleteme* paths
    elif count > 1:
        tmp = []
        dupeDict[sha] = {}
        for x in range(0, len(shaMatch)):
            print(x, shaMatch[x])
            # print("len:", len(shaMatch[x][2]), shaMatch[x][2])
            tmp.append(len(shaMatch[x][2]))
            # using sha key add files to dupeDict
            dupeDict[sha][x] = shaMatch[x][1:]
        shtInd = tmp.index(min(tmp))
        # print("min:", shtInd, shaMatch[shtInd][2])
        filesToProcess.append(shaMatch[shtInd][1:])

print("len(emptyDir):      ", len(emptyDir))
print("len(filesToProcess):", len(filesToProcess))
print("len(dupeDict):      ", len(dupeDict))

# assess emptyDir - can files be added back in - use for scanCMIP3 test dirs
# assess !noDateFile(77) - can model/exp/table matches be found
# assess !fileReadError(9) - can kludges be found

pdb.set_trace()


# %% create lists to catch
srcIds = []
srcIdsFx = []
varIds = []

# %% start looping
for key in dirList:
    print("key:", key)
    if key in [
        "/p/css03/esgf_publish/cmip3/ipcc/20c3m/atm/da/rlus/miub_echo_g/run1",
        "/p/css03/esgf_publish/cmip3/ipcc/data12/sresa2/ocn/mo/tos/ingv_echam4/run1",
        "/p/css03/esgf_publish/cmip3/ipcc/data12/sresa2/ocn/mo/usi/ingv_echam4/run1",
        "/p/css03/esgf_publish/cmip3/ipcc/data12/sresa2/ocn/mo/vsi/ingv_echam4/run1",
        "/p/css03/esgf_publish/cmip3/ipcc/data12/sresa2/ocn/mo/zos/ingv_echam4/run1",
        "/p/css03/esgf_publish/cmip3/ipcc/data17/20c3m/atm/da/rlus/miub_echo_g/run1",
        "/p/css03/esgf_publish/cmip3/ipcc/data7/amip/atm/mo/tro3/miroc3_2_medres/run1",  # bad time
        "/p/css03/esgf_publish/cmip3/ipcc/data7/slabcntl/ocn/mo/qflux/giss_model_e_r/run1",  # bad time units
        "/p/css03/esgf_publish/cmip3/ipcc/slabcntl/ocn/mo/qflux/giss_model_e_r/run1",
    ]:
        continue  # bad indexing, will be fixed in >230723_cmip3.json
    tmp = a[key]
    fileKeys = tmp.keys()  # total file counts
    for fileKey in fileKeys:
        pass

    print(tmp, "len(tmp):", len(tmp))
    print("----------")
    # pdb.set_trace()
    pathBits = key.split("/")
    # for ref cm3Drs = "/p/css03/esgf_publish/cmip3/ipcc/$dataX/$exp_id/$realm/$freq/$var_id/$source_id/$ripf"
    expId, actId = matchExperiment(pathBits)
    print("activity_id:", actId)
    expId = expId[0]
    print("experiment_id:", expId)
    realm = matchRealm(pathBits)[0]
    print("realm:", realm)
    freqId, varId, srcId = matchFrequency(pathBits)
    freqId = freqId[0]
    print("frequency_id:", freqId)
    print("var_id:", varId)
    srcId = fixSource(srcId)
    print("source_id:", srcId)
    if varId not in varIds:
        varIds.append(varId)
    instId = matchInst(srcId)
    print("source_id:", srcId, "->", fixSource(srcId))
    # if srcId in ["BCC-CM1"]:
    #    pdb.set_trace()
    if srcId not in srcIds:
        srcIds.append(srcId)
        srcIdsFx.append(fixSource(srcId))
    memberId = matchRun(pathBits)[0]
    print("member_id:", memberId)
    # pdb.set_trace()
    # pdb.set_trace()
    fileName = list(a[key].keys())
    print("fileName:", fileName)
    # tableId = matchTable(fileName[0])  # can multi-file directories be scanned?
    tableId = matchTable(fileName)
    print("table_id:", tableId)
    date = a[key][fileName[0]]["date"]
    print("date1:", date)
    verId = date[0].replace("-", "")
    print("version_id:", verId)
    print("----------")
    print(
        "DRS:",
        os.path.join(
            "CMIP3",
            actId,
            instId,
            srcId,
            expId,
            memberId,
            tableId,
            varId,
            "gn",
            verId,
        ),
    )
    # <mip_era>/<activity_id>/<institution_id>/<source_id>/<experiment_id>/
    # <member_id>/<table_id>/<variable_id>/<grid_label>/<version>
    startTime = a[key][fileName[0]]["time0"]
    print("startTime:", startTime)
    endTime = a[key][fileName[0]]["timeN"]
    print("endTime:", endTime)
    if startTime is None:
        print("startTime is None")
        fileBits = [
            varId,
            tableId,
            srcId,
            expId,
            memberId,
            "gn",
        ]
    else:
        print("startTime else")
        fileBits = [
            varId,
            tableId,
            srcId,
            expId,
            memberId,
            "gn",
            "-".join([formatDate(startTime), formatDate(endTime)]),
        ]
    print(
        "Filename:",
        "".join(["_".join(fileBits), ".nc"]),
    )
    # <variable_id>_<table_id>_<source_id>_<experiment_id >_<member_id>_<grid_label>[_<time_range>].nc
    print("----------")

print("----------")
srcIds.sort()
print("source_ids:", len(srcIds), srcIds)
srcIdsFx.sort()
print("source_ids-Fx:", len(srcIdsFx), srcIdsFx)
print("----------")
varIds.sort()
print("variable_ids:", len(varIds), varIds)
