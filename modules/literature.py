import requests, time
ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
def pubmed_search(condition, intervention, maxids=50, delay=0.34):
    q = f'("{condition}"[Title/Abstract]) AND ("{intervention}"[Title/Abstract])'
    params = {"db":"pubmed","retmode":"json","retmax":maxids,"term":q}
    r = requests.get(ESEARCH, params=params, timeout=30); r.raise_for_status()
    js = r.json(); time.sleep(delay); return js.get("esearchresult", {}).get("idlist", [])
def pubmed_summaries(pmids):
    if not pmids: return []
    params={"db":"pubmed","retmode":"json","id":",".join(pmids)}
    r=requests.get(ESUMMARY, params=params, timeout=30); r.raise_for_status()
    js=r.json(); out=[]
    for pid,meta in js.get("result", {}).items():
        if pid=="uids": continue
        out.append({"pmid":pid,"title":meta.get("title"),"pubdate":meta.get("pubdate"),"sources":meta.get("source")})
    return out
