from owlready2 import *
from rdflib import Graph
from requests.structures import CaseInsensitiveDict
from shutil import copyfileobj
from alive_progress import alive_bar
import random
import os
import owlready2
import requests
import json
import argparse

OUTPUT_DIR = './analysis/'

def init():
    """
    Initializes owlready Java path, otnology path and random seed
    """
    owlready2.JAVA_EXE = "java"
    onto_path.append("./")
    random.seed(357)


def get_random_classes_fair_foops(n, ontology_dir, fair_foops):
    """Get n random classes from given ontology and generate fair and foops report

    Args:
        n (int): number of classes to get
        ontology_dir (string): path to ontology file
        fair_foops (bool): generate fair/foops
    """    
    ontname, ontpath, path = name_path_ontpath(ontology_dir=ontology_dir,filename=".txt")
    ontname = ontology_dir.split(os.path.sep)[-1].split(".")[0]
    try:
        onto = get_ontology("file://"+ontology_dir).load()
    except Exception as e:
        with open(path +"/"+ontname+"Loadingexception.txt", 'w') as f:
                f.write(str(e))
        return
    if onto.base_iri and fair_foops:
        get_foops_report(ontology_dir, onto.base_iri)
        get_faircheck_report(ontology_dir, onto.base_iri)
    classes = random.sample(list(onto.classes()),k=n)
    os.makedirs(path, exist_ok=True)
    if( os.path.isfile(ontpath) and not os.path.getsize(ontpath) <= 0):
        return
    with open(str(ontpath), 'w') as f:
        f.write("Classes:" + str(len(list(onto.classes()))))
        f.write('\n')
        f.write("Annotation properties:" + str(len(list(onto.annotation_properties()))))
        f.write('\n')
        f.write("Data properties:" + str(len(list(onto.data_properties()))))
        f.write('\n')
        f.write("Object properties:" + str(len(list(onto.object_properties()))))
        f.write('\n')
        f.write("total properties:" + str(len(list(onto.properties()))))
        f.write('\n')
        for cl in classes:
            f.write(str(cl))
            f.write('\n')
            f.write(str(cl.comment))
            f.write('\n')

def get_used_onts( ontology_dir):
    """Get every ontology that is used in given ontology via namespace

    Args:
        ontology_dir (str): path to ontology file
    """    
    ontname, ontpath, path = name_path_ontpath(ontology_dir=ontology_dir,filename="USEDONTS.txt")
    try:
        g = Graph()
        g.parse(ontology_dir)
    except Exception as e:
        with open(path +"/"+ontname+"Loadingexception.txt", 'w') as f:
                f.write(str(e))
        return
    used_onts = list(g.namespace_manager.namespaces())
    os.makedirs(path, exist_ok=True)
    if( os.path.isfile(ontpath) and not os.path.getsize(ontpath) <= 0):
        return
    with open(str(ontpath), 'w') as f:
        f.write("USED_Onts:" + str(len(used_onts)))
        f.write('\n')
        for ontname,iri in used_onts:
            f.write(ontname + ": " + str(iri))
            f.write('\n')


def get_ont_files(dir):
    """Get all ontology files ending with owl and ttl in a given dir

    Args:
        dir (str): dir to search for files

    Returns:
        list: all paths to the ontology files
    """    
    return  [os.path.join(dp, f) for dp, dn, filenames in os.walk(dir) for f in filenames if os.path.splitext(f)[1] == '.owl' or os.path.splitext(f)[1] == '.ttl']

def get_all_for_all_onts_in_dir(dir):
    """Generate everything(foops,fair,oops,used_onts, random classes, reasoner) for every ontology in the given dir

    Args:
        dir (str): path to ontology file
    """    
    onts = get_ont_files(dir)
    with alive_bar(len(onts), ctrl_c=False, title=f'Processed Onts ')  as bar:
        for o in onts:
            if(".ttl" in o):
                o = ttl_to_owl(o)
            try:
                get_used_onts(o)
                get_random_classes_fair_foops(5, o, True)
                get_oops_pitfalls(o)
            except Exception as e:  
                pass
            run_reasoner(o)
            bar()


def run_reasoner(ontology_dir):
    """Run reasoner for given ontology

    Args:
        ontology_dir (str): path to ontology file
    """    
    ontname, ontpath, path = name_path_ontpath(ontology_dir=ontology_dir,filename="reasonererror.txt")
    onto = get_ontology("file://"+ontology_dir).load()
    try:
        with onto:     
            sync_reasoner()
    except Exception as e:
        with open(ontpath, 'w') as f:
            f.write(str(e))

        

def ttl_to_owl(dir):
    """Converts ttl ontology to owl ontology

    Args:
        dir (str): path to ttl ontology file

    Returns:
        str: path to owl ontology file
    """    
    g= Graph()
    g.parse(dir)
    g.serialize(format="pretty-xml", destination=dir.split(".ttl")[0]+".owl")
    return dir.split(".ttl")[0]+".owl"

def get_oops_pitfalls(ontology_dir):
    """Generate OOPS report via sourcecode. Adapted from  https://github.com/OnToology/oops-report/blob/master/main.py

    Args:
        ontology_dir (str): path to ontology file
    """    
    ontname, ontpath, path = name_path_ontpath(ontology_dir=ontology_dir,filename="OOPS.txt")
    while(not os.path.isfile(ontpath) or os.path.getsize(ontpath) <= 0):
        g= Graph()
        g.parse(ontology_dir)
        v = g.serialize(format="xml")
        url = "https://oops.linkeddata.es/rest"
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <OOPSRequest>
          <OntologyUrl></OntologyUrl>
          <OntologyContent>%s</OntologyContent>
            <Pitfalls>2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 19, 20, 21, 22, 24, 25, 25, 26, 27, 28, 29</Pitfalls>
            <OutputFormat>XML</OutputFormat>
        </OOPSRequest>""" % (v)
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/xml"
        headers = {'Content-Type':'rdf/xml'}
        os.makedirs(path, exist_ok=True)
        with open(ontpath, 'wb') as f:
            with requests.post(url, headers=headers, data=xml_content, stream=True)as reply:
                reply.raw.decode_content = True
                copyfileobj(reply.raw,f)
        #sum_oops(path, "OOPSsum")

def get_oops_pitfalls2(ontology_dir, iri):
    """Generate OOPS report via sourcecode. Adapted from  https://github.com/OnToology/oops-report/blob/master/main.py

    Args:
        ontology_dir (str): path to ontology file
    """    
    ontname, ontpath, path = name_path_ontpath(ontology_dir=ontology_dir,filename="OOPS.txt")
    while(not os.path.isfile(ontpath) or os.path.getsize(ontpath) <= 0):
        url = "https://oops.linkeddata.es/rest"
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <OOPSRequest>
          <OntologyUrl>%s</OntologyUrl>
          <OntologyContent></OntologyContent>
            <Pitfalls>2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 19, 20, 21, 22, 24, 25, 25, 26, 27, 28, 29</Pitfalls>
            <OutputFormat>XML</OutputFormat>
        </OOPSRequest>""" % (iri)
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/xml"
        headers = {'Content-Type':'rdf/xml'}
        os.makedirs(path, exist_ok=True)
        with open(ontpath, 'wb') as f:
            with requests.post(url, headers=headers, data=xml_content, stream=True)as reply:
                reply.raw.decode_content = True
                copyfileobj(reply.raw,f)
        #sum_oops(path, "OOPSsum")

def get_foops_report(ontology_dir, iri):
    """Generate FOOPS report via iri.

    Args:
        ontology_dir (str): path to ontology file
        iri (str): ontology iri
    """    
    ontname, ontpath, path = name_path_ontpath(ontology_dir=ontology_dir,filename="FOOPS.json")
    while(not os.path.isfile(ontpath) or os.path.getsize(ontpath) <= 0):
        url = "https://foops.linkeddata.es/assessOntology"
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        os.makedirs(path, exist_ok=True)
        with open(ontpath, 'w') as f:
            with requests.post(url, headers=headers, json={"ontologyUri": str(iri)}, stream=True)as reply:
                #reply.raw.decode_content = True
                json.dump(reply.json(),f)
                #copyfileobj(reply.raw,f)

def name_path_ontpath(ontology_dir, filename):
    """helper function generating ontname, ontpath and path from path to ontology file and filename

    Args:
        ontology_dir (str): path to ontology file
        filename (str): file name

    Returns:
        str: 3 strings, ont name, ont path and path
    """    
    ontname = ontology_dir.split(os.path.sep)[-1].split(".")[0]
    if("DABGEO" in ontology_dir):
        path =os.path.dirname(OUTPUT_DIR +"dabgeo/")
        ontpath = OUTPUT_DIR + "dabgeo/"+ontname+filename
    else:
        path =os.path.dirname(OUTPUT_DIR+ontname+"/")
        ontpath = OUTPUT_DIR+ontname+"/"+ontname+filename
    return ontname, ontpath, path

def get_faircheck_report(ontology_dir, iri):
    """Generate FAIR Check from IRI

    Args:
        ontology_dir (str): path to ontology file
        iri (str): ontology iri
    """    
    ontname, ontpath, path = name_path_ontpath(ontology_dir=ontology_dir,filename="FAIRCHECK.json")
    while(not os.path.isfile(ontpath) or os.path.getsize(ontpath) <= 0):
        url = "https://fair-checker.france-bioinformatique.fr/api/check/metrics_all?url={0}".format(urllib.parse.quote(str(iri), safe=''))
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        os.makedirs(path, exist_ok=True)
        with open(ontpath, 'w') as f:
            with requests.get(url, headers=headers, stream=True)as reply:
                json.dump(parse_faircheck_json(reply.json()),f)
            

def parse_faircheck_json(payload):
    """Helper Function to parse the received FAIR report and generate a MEAN FAIR Score

    Args:
        payload (str): json payload

    Returns:
        str: new json payload
    """    
    results ={}
    for metric in payload:
        if str(metric["metric"])[0] not in results:
            results[str(metric["metric"])[0]] = int(metric["score"])
        else:
            results[str(metric["metric"])[0]] += int(metric["score"])
    results["F"] /= 4
    results["I"] /= 3
    results["R"] /= 3
    results = {"mean" : results}
    payload.insert(0,results)
    return payload

def sum_class_prop(dir,filename):
    """Sums up the classes and properties of all ontology reports in a given directory and saves it in filename

    Args:
        dir (str): path to ontology rports (generated via get_random_classes_fair_foops)
        filename (str): filename where the sum should be saved
    """    
    files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(dir) for f in filenames if os.path.splitext(f)[1] == '.txt' and "OOPS" not in os.path.splitext(f)[0]and "exception" not in os.path.splitext(f)[0]and "USEDONTS" not in os.path.splitext(f)[0] and filename not in os.path.splitext(f)[0]]  
    sum_classes = 0
    sum_anot_prop = 0
    sum_data_prop = 0
    sum_object_prop = 0
    sum_total_prop = 0
    with alive_bar(len(files), ctrl_c=False, title=f'Processed Onts')  as bar:
        for file in files:
            with open(file, "r") as f:
                sum_classes += int(f.readline().split(':')[1])
                sum_anot_prop += int(f.readline().split(':')[1])
                sum_data_prop += int(f.readline().split(':')[1])
                sum_object_prop += int(f.readline().split(':')[1]) 
                sum_total_prop += int(f.readline().split(':')[1])
            bar()
    with open(dir+filename+'.txt', 'w') as f:
        f.write("Classes:" + str(sum_classes))
        f.write('\n')
        f.write("Annotation properties:" + str(sum_anot_prop))
        f.write('\n')
        f.write("Data properties:" + str(sum_data_prop))
        f.write('\n')
        f.write("Object properties:" + str(sum_object_prop))
        f.write('\n')
        f.write("total properties:" + str(sum_total_prop))
        f.write('\n')
            

def sum_used_onts(dir,filename):
    """Sums up the used ontologies of all ontology reports in a given directory and saves it in filename

    Args:
        dir (str): path to ontology rports (generated via get_used_onts)
        filename (str): filename where the sum should be saved
    """   
    files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(dir) for f in filenames if os.path.splitext(f)[1] == '.txt' and "USEDONTS" in os.path.splitext(f)[0]and filename not in os.path.splitext(f)[0]]  
    results = {}
    with alive_bar(len(files), ctrl_c=False, title=f'Processed Onts ')  as bar:
        for file in files:
            with open(file, "r") as f:
                f.readline()
                line = f.readline()
                i = 0
                while line:
                    abrv = line.split(":")[0]
                    iri = line.split(":",1)[1]
                    if abrv:
                        results[str(abrv)] = str(iri)
                    elif "NO name" + str(i) in results.keys() and results["NO name" + str(i)] != str(iri):
                        results["NO name" + str(i)] = str(iri)
                        i = i + 1
                    elif "NO name" + str(i) not in results.keys():
                        results["NO name" + str(i)] = str(iri)
                        i = i + 1
                    line = f.readline()
            bar()
    with open(dir +filename+'.txt', 'w') as f:
        f.write("namespace --- iri" + " USED_Onts:" + str(len(results)))
        for key, value in results.items():
            f.write('\n')
            f.write(key + "---" + value)

def sum_oops(dir,filename):
    """Sums up the used ontologies of all ontology reports in a given directory and saves it in filename

    Args:
        dir (str): path to ontology rports (generated via get_used_onts)
        filename (str): filename where the sum should be saved
    """   
    files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(dir) for f in filenames if os.path.splitext(f)[1] == '.txt' and "OOPS" in os.path.splitext(f)[0]and filename not in os.path.splitext(f)[0]]  
    results = {"Minor":0, "Important":0}
    with alive_bar(len(files), ctrl_c=False, title=f'Processed Onts ')  as bar:
        for file in files:
            with open(file, "r") as f:
                for line in f.readlines():
                    if "Importance" in line and "Minor" in line:
                        results["Minor"] += 1
                    elif "Importance" in line and "Important" in line:
                        results["Important"] +=1
            bar()
    with open(dir +filename+'.txt', 'w') as f:
        f.write("namespace --- iri" + " OOPS:" + str(len(results)))
        for key, value in results.items():
            f.write('\n')
            f.write(key + "---" + str(value))

def mean_fair_foops(dir, filename):
    """Means up the Fair and Foops reports of all ontologies in a given directory and saves it in filename

    Args:
        dir (str): path to ontology rports (generated via get_fair and get_foops)
        filename (str): filename where the sum should be saved
    """ 
    files_foops = [os.path.join(dp, f) for dp, dn, filenames in os.walk(dir) for f in filenames if os.path.splitext(f)[1] == '.json' and "FOOPS" in os.path.splitext(f)[0] and filename not in os.path.splitext(f)[0]]
    files_fair = [os.path.join(dp, f) for dp, dn, filenames in os.walk(dir) for f in filenames if os.path.splitext(f)[1] == '.json' and "FAIR" in os.path.splitext(f)[0]and filename not in os.path.splitext(f)[0]]  
    results = {"FOOPS":0, "F":0, "A":0, "I":0, "R":0}
    with alive_bar(len(files_foops + files_fair), ctrl_c=False, title=f'Processed Onts ')  as bar:
        for file in files_foops + files_fair:
            with open(file, "r") as f:
                data = json.load(f)
                if("FOOPS" in file):
                    results["FOOPS"] += data["overall_score"]
                else:
                    for key, value in data[0]["mean"].items():
                        results[key] += value
            bar()
    results["FOOPS"] /= len(files_foops)
    results["F"] /= len(files_fair)
    results["A"] /= len(files_fair)
    results["I"] /= len(files_fair)
    results["R"] /= len(files_fair)
    with open(dir +filename+'.json', 'w') as f:
        json.dump(results,f)

def get_missing_dabgeo():
    """Helper function for my thesis, not used in script
    """  
    dir = './analysis/dabgeo/'
    dir2 = './DABGEO_v1.0/'
    filename = "missing.txt"
    used = [os.path.join(dp, f) for dp, dn, filenames in os.walk(dir) for f in filenames if os.path.splitext(f)[1] == '.txt' and "USEDONTS" in os.path.splitext(f)[0]] 
    onts = [os.path.join(dp, f) for dp, dn, filenames in os.walk(dir2) for f in filenames if os.path.splitext(f)[1] == '.owl']  
    exceptions = [os.path.join(dp, f) for dp, dn, filenames in os.walk(dir) for f in filenames if os.path.splitext(f)[1] == '.txt' and "Loadingexception" in os.path.splitext(f)[0]and filename not in os.path.splitext(f)[0]] 
    all_json =  [os.path.join(dp, f) for dp, dn, filenames in os.walk(dir) for f in filenames if os.path.splitext(f)[1] == '.json']  
    all_txt = [os.path.join(dp, f) for dp, dn, filenames in os.walk(dir) for f in filenames if os.path.splitext(f)[1] == '.txt']  
    foopsl = []
    oopsl = []
    fairl = []
    usedl = []
    results = {"total":len(onts),"LoadingError":len(exceptions), "oops":0, "foops":0, "fair":0}
    for ont in onts:
        ont = ont.split(".")[-2].split(os.path.sep)[-1]
        a = False
        for oops in all_txt:
            if "OOPS" in oops and ont in oops:
                a = True
                continue
        if not a:
            oopsl.append(ont)
        a = False
        for oops in all_json:
            if "FOOPS" in oops and ont in oops:
                a = True
                continue
        if not a:
            foopsl.append(ont)
        a = False
        for oops in all_json:
            if "FAIR" in oops and ont in oops:
                a = True
                continue
        if not a:
            fairl.append(ont)
        a = False
        for oops in used:
            if "USEDONTS" in oops and ont in oops:
                a = True
                continue
        if not a:
            usedl.append(ont)
    results["fair"] = len(fairl)
    results["oops"] = len(oopsl)
    results["foops"] = len(foopsl)
    """
    with open(dir +filename+'.txt', 'a') as f:
        for key, value in results.items():
            f.write('\n')
            f.write(key + "---" + str(value))
        f.write("\n---------------------------------------------------------\n")
        f.write("FAIR:\n")
        for line in fairl:
            f.write(line+"\n")
        f.write("---------------------------------------------------------\n")
        f.write("FOOPS:\n")
        for line in foopsl:
            f.write(line+"\n")
        f.write("---------------------------------------------------------\n")
        f.write("OOPs:\n")
        for line in oopsl:
            f.write(line+"\n")
        f.write("---------------------------------------------------------\n")
        f.write("Loading:\n")
        for line in exceptions:
            f.write(line+"\n")"""
    try_again(oopsl,foopsl,fairl,onts, exceptions)

def listhelper(lista,stringb):
    """helper function for get_missing_dabgeo
    """
    for l in lista:
        if stringb in l:
            return l

def try_again(oops,foops,fair, onts, e):
    """helper function for get_missing_dabgeo
    """
    for ont in foops:
        ontology_dir = listhelper(onts, ont)
        g= Graph()
        g.parse(ontology_dir)
        res = ["common-domain/", "variant-domain/", "domain-task/"]
        if int(ontology_dir.split(os.path.sep)[0].split("/")[-1][0])-1 == 2:
            iri = "https://innoweb.mondragon.edu/ontologies/dabgeo/" + res[int(ontology_dir.split(os.path.sep)[0].split("/")[-1][0])-1] + ontology_dir.split(os.path.sep)[1] + "/" +ontology_dir.split(os.path.sep)[2] + "/" +ontology_dir.split(os.path.sep)[3] + "/1.0/"
        else:
            iri = "https://innoweb.mondragon.edu/ontologies/dabgeo/" + res[int(ontology_dir.split(os.path.sep)[0].split("/")[-1][0])-1] + ontology_dir.split(os.path.sep)[1] + "/" +ontology_dir.split(os.path.sep)[2] + "/1.0/"
        get_foops_report(ont, iri)
    for ont in fair:
        ontology_dir = listhelper(onts, ont)
        g= Graph()
        g.parse(ontology_dir)
        res = ["common-domain/", "variant-domain/", "domain-task/"]
        if int(ontology_dir.split(os.path.sep)[0].split("/")[-1][0])-1 == 2:
            iri = "https://innoweb.mondragon.edu/ontologies/dabgeo/" + res[int(ontology_dir.split(os.path.sep)[0].split("/")[-1][0])-1] + ontology_dir.split(os.path.sep)[1] + "/" +ontology_dir.split(os.path.sep)[2] + "/" +ontology_dir.split(os.path.sep)[3] + "/1.0/"
        else:
            iri = "https://innoweb.mondragon.edu/ontologies/dabgeo/" + res[int(ontology_dir.split(os.path.sep)[0].split("/")[-1][0])-1] + ontology_dir.split(os.path.sep)[1] + "/" +ontology_dir.split(os.path.sep)[2] + "/1.0/"
        get_faircheck_report(ont, iri)
    for ont in oops:
        ontology_dir = listhelper(onts, ont)
        g= Graph()
        g.parse(ontology_dir)
        res = ["common-domain/", "variant-domain/", "domain-task/"]
        if int(ontology_dir.split(os.path.sep)[0].split("/")[-1][0])-1 == 2:
            iri = "https://innoweb.mondragon.edu/ontologies/dabgeo/" + res[int(ontology_dir.split(os.path.sep)[0].split("/")[-1][0])-1] + ontology_dir.split(os.path.sep)[1] + "/" +ontology_dir.split(os.path.sep)[2] + "/" +ontology_dir.split(os.path.sep)[3] + "/1.0/"
        else:
            iri = "https://innoweb.mondragon.edu/ontologies/dabgeo/" + res[int(ontology_dir.split(os.path.sep)[0].split("/")[-1][0])-1] + ontology_dir.split(os.path.sep)[1] + "/" +ontology_dir.split(os.path.sep)[2] + "/1.0/"
        get_oops_pitfalls2(ont, iri)
    for ont in e:
        ontology_dir = listhelper(onts, ont)
        g= Graph()
        g.parse(ontology_dir)
        break


parser = argparse.ArgumentParser(prog = 'OntMetaScript',
                    description = 'Gather Ontology Metadata and Analysis from Ont files',
                    epilog = 'Text at the bottom of help')
parser.add_argument("-o", "--output", help="Set output directory.",default='./analysis/')
parser.add_argument("-a", "--analysis", help="Analyses all owl or ttl ontologies in the supplied directory and saves them.")
parser.add_argument("-rf", "--random_classes_fair_foops", help=" n, ont_dir, bool Gets a given number n of random classes from the ontology file dir and gets FOOPS and FAIR report if bool is True. Also generates a normal report with the random classes in it", nargs=3)
parser.add_argument("-fo", "--foops", help="Ont_dir, iri.Generate FOOPS Report of given ontology.",nargs=2)
parser.add_argument("-fa", "--fair", help="Ont_dir, iri.Generate FAIR Report of given ontology, also generates a Mean fair score.",nargs=2)
parser.add_argument("-oo", "--oops", help="Ont_dir.Generate OOPS Report of given ontology.")
parser.add_argument("-r", "--reasoner", help="Ont_dir.Checks if Reasoner can be run.")
parser.add_argument("-so", "--sum_onts", help="Dir, Name. Sums up the used onts of all ontologies in a dir and saves them in a file named Name. Used Ontologies report needed.",nargs=2)
parser.add_argument("-scp", "--sum_classes_prop",help="Dir, Name. Sums up the classes and properties of all ontologies in a dir and saves them in a file named Name.Normal Report needed",nargs=2)
parser.add_argument("-m", "--mean_fair_foops", help="Dir, Name. Means the Fair and foops score of all ontologies in a dir and saves them in a file named Name. FOOPS Report and FAIR Report needed",nargs=2)
args = parser.parse_args()

init()

if args.output:
    OUTPUT_DIR=args.output
if args.analysis:
    get_all_for_all_onts_in_dir(args.analysis)
if args.random_classes_fair_foops:
    try:
        n = int(args.random_classes_fair_foops[0])
        dir = args.random_classes_fair_foops[1]
        bo = bool(args.random_classes_fair_foops[2])
        get_random_classes_fair_foops(n,dir,bo)
    except Exception :
        print("INT, DIR, boolean needed")
if args.foops:
    try:
        get_foops_report(args.foops[0],args.foops[1])
    except Exception :
        print("DIR, IRI needed")
if args.fair:
    try:
        get_faircheck_report(args.fair[0],args.fair[1])
    except Exception :
        print("DIR, IRI needed")
if args.oops:
    try:
        get_faircheck_report(args.oops)
    except Exception :
        print("DIR needed")
if args.reasoner:
    try:
        get_faircheck_report(args.reasoner)
    except Exception :
        print("DIR needed")
if args.sum_onts:
    try:
        sum_used_onts(args.sum_onts[0],args.sum_onts[1])
    except Exception :
        print("DIR, name needed")
if args.sum_classes_prop:
    try:
        sum_class_prop(args.sum_classes_prop[0],args.sum_classes_prop[1])
    except Exception :
        print("DIR, name needed")
if args.mean_fair_foops:
    try:
        mean_fair_foops(args.mean_fair_foops[0],args.mean_fair_foops[1])
    except Exception :
        print("DIR, name needed")
