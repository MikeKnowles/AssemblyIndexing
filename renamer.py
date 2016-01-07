#!/usr/bin/env python
__author__ = 'mikeknowles'


class Fixer:
    def __init__(self, fname, path):
        self.fname = fname
        self.path = path
        import zipfile
        from xml.etree.ElementTree import iterparse
        z = zipfile.ZipFile(self.fname)
        strings = [el.text for e, el in iterparse(z.open('xl/sharedStrings.xml')) if el.tag.endswith('}t')]
        self.rows = []
        row = {}
        value = ''
        for e, el in iterparse(z.open('xl/worksheets/sheet1.xml')):
            if el.tag.endswith('}v'):  # <v>84</v>
                value = el.text
            if el.tag.endswith('}c'):  # <c r="A3" t="s"><v>84</v></c>
                if el.attrib.get('t') == 's':
                    value = strings[int(value)]
                letter = el.attrib['r']  # AZ22
                while letter[-1].isdigit():
                    letter = letter[:-1]
                row[letter] = value
                value = ''
            if el.tag.endswith('}row'):
                if row != {}:
                    self.rows.append(row)
                    row = {}
        self.rows.pop(0)
        from glob import glob
        import json
        self.n50dict = {}
        flist = glob(path+"/*.json")
        for f in flist:
            with open(f) as e:
                report = json.load(e)
            floc = f.replace("JsonReports", "Assemblies").replace("metadataReport.json", "filteredAssembled.fasta")
            try:
                self.n50dict[(report["2.Assembly"]["TotalLength"],
                              "%.2f" % float(report["1.General"]["MeanInsertSize"]))] =\
                    (floc, f)
            except KeyError:
                print f, "JSON malformatted"
            except ValueError:
                pass

    def SeqFix(self, seqid):
        a = str(seqid).split("-")
        a[2] = str(a[2]).zfill(4)
        return "-".join(a)

    def compare(self):
        import re
        from os.path import isfile
        for row in self.rows:
            try:
                species = re.sub('\W+','_', row["F"].rstrip())
                a = self.SeqFix(row["A"])
                fname = self.n50dict[(str(row["U"]), "%.2f" % float(row["V"]),)][0]
                src = "%s/IndexedAssemblies/%s_%s.fasta" % ("/".join(fname.split("/")[:-2]), a, species)
                if not isfile(src):
                    print src, fname
                    oldhandle = open(fname)
                    with open(src, "w") as w:
                        for line in oldhandle:
                            if line.startswith(">"):
                                line = ">%s_%s" % (a, "_".join(line.split("_")[-7:]))
                            w.write(line)
                    oldhandle.close()
            except (KeyError, ValueError):
                pass
                print "Unsuccessful", "SEQ ID:", row["A"], "Common Name:", row["B"]
            except IndexError:
                print row["A"]
            except IOError:
                print self.n50dict[(str(row["U"]), "%.2f" % float(row["V"]),)], "Does not exist"

    def MoveJson(self):
        from shutil import copyfile
        from os.path import isfile
        for row in self.rows:
            if "V" in row:
                if row["V"] not in ('','N/A'):
                    n50key = (str(row["U"]), "%.2f" % float(row["V"]),)
                    if n50key in self.n50dict:
                        fjson = self.n50dict[n50key][1]
                        a = self.SeqFix(row["A"])
                        newjson = "%s/IndexedJson/%s.json" % ("/".join(fjson.split("/")[:-2]), a)
                        if not isfile(newjson):
                            copyfile(fjson, newjson)
                    else:
                        print "Record:", row["A"], n50key


def Extractor(fpath, val, dicttuplist, out):
    from glob import glob
    from json import load
    from os import system
    flist = glob(fpath + "/*.json")
    genomes = []
    for f in flist:
        with open(f) as e:
            report = load(e)
        floc = f.replace("IndexedJson", "IndexedAssemblies").replace(".json", "*.fasta")
        indict = False
        if len(val) == len(dicttuplist):
            for i in range(len(val)):
                try:
                    if val[i] in report[dicttuplist[i][0]][dicttuplist[i][1]]:
                        indict += 1
                    elif "averageDepthofCov" in val[i]:
                        if val[i] <= report[dicttuplist[i][0]][dicttuplist[i][1]]:
                            indict += 1
                    elif "NumContigs" in val[i]:
                        if val[i] >= report[dicttuplist[i][0]][dicttuplist[i][1]]:
                            indict += 1
                except KeyError:
                    print f, "JSON malformatted"
                except ValueError:
                    pass
        if indict == len(val):
            genomes.append(floc)
    for j in genomes:
        print j
        system(" cp %s %s" % (j, out))


# rows = Fixer("/Users/mike/Dropbox/WGS tracking/Combined Data Reports.xlsx",
#              "/nas/akoziol/WGS_Spades/AssemblyData/JsonReports")
# rows.compare()
# rows.MoveJson()
import os

# os.mkdir("/nas/akoziol/Pipeline_development/ePFGE/kSNP/Ecoli/")
#os.mkdir("/nas/akoziol/Pipeline_development/ePFGE/kSNP/Salmonella/99")
Extractor("/nas/akoziol/WGS_Spades/AssemblyData/IndexedJson",
          ["11", "S517", "Listeria"],
          [("1.General", "MLST_sequenceType"), ("3.Run", "I5IndexID"), ("1.General", "referenceGenome")],
          "/nas/akoziol/Pipeline_development/ePFGE/kSNP/Salmonella/99")