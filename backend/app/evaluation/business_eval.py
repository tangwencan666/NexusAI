import argparse,json
from pathlib import Path

def score(path:str)->dict[str,float]:
    rows=[json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()];keys=[k for k in rows[0] if k not in {"id","type"}];return {"dataset_size":len(rows),**{k:sum(bool(x[k]) for x in rows)/len(rows) for k in keys}}
def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument("--dataset",required=True);args=parser.parse_args();result=score(args.dataset)
    for key,value in result.items():print(f"{key}: {value if key=='dataset_size' else f'{value:.4f}'}")
    return 0
if __name__=="__main__":raise SystemExit(main())
