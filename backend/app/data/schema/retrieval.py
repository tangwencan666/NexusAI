import re
from app.data.schema.catalog import TableInfo


class SchemaRetriever:
    def search(self, question: str, tables: list[TableInfo], top_k: int = 8) -> list[TableInfo]:
        terms=set(re.findall(r"[\w]+",question.lower()))
        aliases={"sales":{"order","orders","amount","revenue"},"revenue":{"order","amount"},"region":{"region"},"customer":{"customer"},"product":{"product"},"monthly":{"ordered_at","month"}}
        expanded=set(terms)
        for term in terms: expanded |= aliases.get(term,set())
        scored=[]
        for table in tables:
            haystack=" ".join([table.table,table.description or "",*[c.name+" "+(c.description or "") for c in table.columns]]).lower()
            score=sum(1 for term in expanded if term in haystack)
            if score:scored.append((score,table))
        return [item for _,item in sorted(scored,key=lambda x:(-x[0],x[1].table))[:top_k]] or tables[:top_k]
