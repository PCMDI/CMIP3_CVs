#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 15:14:34 2023

PJD 24 Jul 2023     - Written to organize CMIP3 data using CMIP6 DRS

Plans
1. Generate keys for all files - scanCMIP3-sha256.py
2. Determine keys to process
3. Process all valid keys
4. Process all !noDateFile entries (using similar inst/mod/exp/table contributions)
5. Process all !fileReadError entries (is there an xarray pipe that fixes it)
6. Process/archive all !badFile entries (along with BCC-CM1, which was unpublished? - Karl)
    - Xujing (Steve K) was involved in CMIP3/ISCCP data generation?

@author: durack1
"""

# %% imports
import json
import os
import pdb


# %% function defs
from CMIP3Lib import (
    fixSource,
    formatDate,
    matchExperiment,
    matchFrequency,
    matchInst,
    matchRealm,
    matchRun,
    matchTable,
)


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
