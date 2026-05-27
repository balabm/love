import sys
import json
import urllib.request
import urllib.parse
import re
import ssl

# Create unverified SSL context to prevent SSL verification failures on Windows systems
try:
    ssl_context = ssl._create_unverified_context()
except AttributeError:
    ssl_context = None

def query_uniprot(query):
    print(f"[UniProt] Querying UniProt for: '{query}'...")
    url = f"https://rest.uniprot.org/uniprotkb/search?query={urllib.parse.quote(query)}&size=3"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LOVE-AGI-Companion/1.0"})
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        results = data.get("results", [])
        if not results:
            print("No UniProt entries found.")
            return
        for entry in results:
            acc = entry.get("primaryAccession", "")
            name = entry.get("uniProtkbId", "")
            genes = [g.get("geneName", {}).get("value", "") for g in entry.get("genes", [])]
            organism = entry.get("organism", {}).get("scientificName", "")
            comments = entry.get("comments", [])
            function = ""
            for c in comments:
                if c.get("commentType") == "FUNCTION":
                    function = " ".join([m.get("value", "") for m in c.get("value", {}).get("texts", [])])
                    break
            print(f"\nAccession: {acc}")
            print(f"Entry Name: {name}")
            print(f"Organism: {organism}")
            if genes:
                print(f"Genes: {', '.join(genes)}")
            if function:
                print(f"Function: {function[:300]}...")
            print("-" * 50)
    except Exception as e:
        print(f"UniProt query error: {e}")

def query_pubmed(query):
    print(f"[PubMed] Querying PubMed for: '{query}'...")
    try:
        # Step 1: Search for IDs
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={urllib.parse.quote(query)}&retmode=json&retmax=3"
        req = urllib.request.Request(search_url, headers={"User-Agent": "LOVE-AGI-Companion/1.0"})
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as resp:
            search_data = json.loads(resp.read().decode("utf-8"))
        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            print("No PubMed publications found.")
            return
        
        # Step 2: Fetch details
        ids = ",".join(id_list)
        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids}&retmode=json"
        req_sum = urllib.request.Request(summary_url, headers={"User-Agent": "LOVE-AGI-Companion/1.0"})
        with urllib.request.urlopen(req_sum, context=ssl_context, timeout=10) as resp:
            summary_data = json.loads(resp.read().decode("utf-8"))
        
        results = summary_data.get("result", {})
        for pm_id in id_list:
            doc = results.get(pm_id, {})
            title = doc.get("title", "")
            authors = ", ".join([a.get("name", "") for a in doc.get("authors", [])])
            source = doc.get("source", "")
            pubdate = doc.get("pubdate", "")
            print(f"\nPMID: {pm_id}")
            print(f"Title: {title}")
            print(f"Authors: {authors}")
            print(f"Source: {source} ({pubdate})")
            print(f"Link: https://pubmed.ncbi.nlm.nih.gov/{pm_id}/")
            print("-" * 50)
    except Exception as e:
        print(f"PubMed query error: {e}")

def query_chembl(query):
    print(f"[ChEMBL] Querying ChEMBL for: '{query}'...")
    url = f"https://www.ebi.ac.uk/chembl/api/data/molecule?pref_name__icontains={urllib.parse.quote(query)}&format=json&limit=3"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LOVE-AGI-Companion/1.0"})
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        molecules = data.get("molecules", [])
        if not molecules:
            print("No ChEMBL molecules found matching name.")
            return
        for mol in molecules:
            chembl_id = mol.get("molecule_chembl_id", "")
            pref_name = mol.get("pref_name", "Unknown Name")
            mol_type = mol.get("molecule_type", "")
            max_phase = mol.get("max_phase", "0")
            synonyms = ", ".join([s.get("molecule_synonym", "") for s in mol.get("molecule_synonyms", []) if s.get("synonym_type") == "TRADE_NAME"][:3])
            print(f"\nChEMBL ID: {chembl_id}")
            print(f"Preferred Name: {pref_name}")
            print(f"Type: {mol_type}")
            print(f"Max Clinical Phase: {max_phase}")
            if synonyms:
                print(f"Trade Names: {synonyms}")
            print(f"Link: https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/")
            print("-" * 50)
    except Exception as e:
        print(f"ChEMBL query error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tools/bio_query.py [uniprot|pubmed|chembl] [query]")
        sys.exit(1)
    
    cmd = sys.argv[1].lower()
    query_str = " ".join(sys.argv[2:])
    
    if cmd == "uniprot":
        query_uniprot(query_str)
    elif cmd == "pubmed":
        query_pubmed(query_str)
    elif cmd == "chembl":
        query_chembl(query_str)
    else:
        print(f"Unknown bio skill command: {cmd}")
        print("Supported commands: uniprot, pubmed, chembl")
        sys.exit(1)
