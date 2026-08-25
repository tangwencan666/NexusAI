import re
from abc import ABC,abstractmethod
from app.documents.models import ContractExtraction,ExtractionResult


class DocumentExtractionProvider(ABC):
    @abstractmethod
    async def extract(self,text:str,document_type:str|None=None)->ExtractionResult:...


def classify(text:str,filename:str="")->str:
    value=(filename+" "+text[:4000]).lower()
    if any(x in value for x in ("agreement","contract","governing law","liability")):return "contract"
    if any(x in value for x in ("invoice","amount due","bill to")):return "invoice"
    if any(x in value for x in ("policy","procedure","shall comply")):return "policy"
    if any(x in value for x in ("report","executive summary","findings")):return "report"
    return "general"


def sentence(text:str,pattern:str)->str|None:
    match=re.search(rf"([^.!?\n]*{pattern}[^.!?\n]*[.!?]?)",text,re.I)
    return match.group(1).strip()[:1000] if match else None


class RuleBasedExtractionProvider(DocumentExtractionProvider):
    async def extract(self,text:str,document_type:str|None=None)->ExtractionResult:
        dtype=document_type or classify(text)
        parties=[]
        party_match=re.search(r"between\s+([A-Z][\w &.,-]+?)\s+and\s+([A-Z][\w &.,-]+?)(?:\.|,|\n)",text,re.I)
        if party_match:parties=[party_match.group(1).strip(),party_match.group(2).strip()]
        date_pattern=r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2}"
        effective=re.search(rf"effective(?: date)?[:\s]+({date_pattern})",text,re.I)
        expiration=re.search(rf"expir(?:es|ation(?: date)?)[:\s]+({date_pattern})",text,re.I)
        amount=re.search(r"(?:USD|\$)\s?[\d,]+(?:\.\d{2})?",text)
        fields=ContractExtraction(parties=parties,effective_date=effective.group(1) if effective else None,expiration_date=expiration.group(1) if expiration else None,payment_terms=sentence(text,r"payment|net\s+\d+"),termination_terms=sentence(text,"terminat"),liability=sentence(text,"liabilit"),confidentiality=sentence(text,"confidential"),governing_law=sentence(text,"governing law"),renewal=sentence(text,"renew"),amount=amount.group(0) if amount else None)
        return ExtractionResult(document_type=dtype,fields=fields)
