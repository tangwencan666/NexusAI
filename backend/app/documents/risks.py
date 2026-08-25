from app.documents.models import ContractExtraction,DocumentRiskResult


class ContractRiskRuleEngine:
    def evaluate(self,text:str,fields:ContractExtraction,page:int|None=None)->list[DocumentRiskResult]:
        value=text.lower();risks=[]
        if "unlimited liability" in value or "all losses" in value:risks.append(DocumentRiskResult(rule_id="unlimited_liability",severity="high",title="Unlimited Liability",description="The agreement appears to impose liability without a cap.",evidence="unlimited liability" if "unlimited liability" in value else "all losses",page=page))
        elif not fields.liability:risks.append(DocumentRiskResult(rule_id="missing_liability_cap",severity="medium",title="Missing Liability Clause",description="No liability provision was extracted.",evidence="No matching liability clause",page=page))
        if fields.renewal and "automatic" in fields.renewal.lower():risks.append(DocumentRiskResult(rule_id="auto_renewal",severity="medium",title="Automatic Renewal",description="The agreement contains automatic renewal language.",evidence=fields.renewal,page=page))
        if fields.payment_terms:
            import re
            days=re.search(r"(?:net|within)\s+(\d+)\s+days",fields.payment_terms,re.I)
            if days and int(days.group(1))>60:risks.append(DocumentRiskResult(rule_id="long_payment_term",severity="medium",title="Long Payment Term",description="Payment term exceeds 60 days.",evidence=fields.payment_terms,page=page))
        if not fields.termination_terms:risks.append(DocumentRiskResult(rule_id="missing_termination",severity="high",title="Missing Termination Clause",description="No termination provision was extracted.",evidence="No matching termination clause",page=page))
        return risks
