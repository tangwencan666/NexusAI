from difflib import SequenceMatcher


class DocumentComparisonService:
    def compare(self,a:str,b:str)->dict:
        left=[x.strip() for x in a.splitlines() if x.strip()];right=[x.strip() for x in b.splitlines() if x.strip()]
        matcher=SequenceMatcher(a=left,b=right);changes=[]
        for tag,i1,i2,j1,j2 in matcher.get_opcodes():
            if tag=="equal":continue
            kind="modified" if tag=="replace" else "removed" if tag=="delete" else "added"
            changes.append({"type":kind,"before":"\n".join(left[i1:i2]),"after":"\n".join(right[j1:j2]),"similarity":SequenceMatcher(None,"\n".join(left[i1:i2]),"\n".join(right[j1:j2])).ratio()})
        return {"summary":{"total":len(changes),"added":sum(x["type"]=="added" for x in changes),"removed":sum(x["type"]=="removed" for x in changes),"modified":sum(x["type"]=="modified" for x in changes)},"changes":changes}
