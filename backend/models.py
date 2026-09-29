"""Pydantic schemas: the single shared vocabulary between ingestion, graph, verifiers and API."""
from typing import Literal, Optional, Union
from pydantic import BaseModel

Kind = Literal["numeric", "free_text", "revision"]

class Document(BaseModel):
    id: str
    kind: Literal["contract", "spec", "drawing"]
    title: str

class Clause(BaseModel):
    id: str; doc_id: str; text: str; parameter: str; kind: Kind
    value: Optional[float] = None; unit: Optional[str] = None
    spec_ref: Optional[str] = None                        # numeric / free_text clauses
    cites_drawing_rev: Optional[str] = None               # revision clauses, e.g. "DWG-114@B"

class SpecReq(BaseModel):
    id: str; doc_id: str; text: str; parameter: str; kind: Kind
    value: Optional[float] = None; tol: Optional[float] = None; unit: Optional[str] = None

class DrawingRev(BaseModel):
    id: str; drawing_id: str; revision: str; date: str
    supersedes: Optional[str] = None                      # id of the older DrawingRev

class Callout(BaseModel):
    id: str; drawing_rev_id: str; parameter: str
    value: Optional[float] = None; unit: Optional[str] = None; text: str

class Corpus(BaseModel):
    documents: list[Document]; clauses: list[Clause]; spec_reqs: list[SpecReq]
    drawing_revs: list[DrawingRev]; callouts: list[Callout]
    warnings: list[str] = []; stats: dict = {}

class Triple(BaseModel):
    id: str; kind: Kind
    clause_id: str; spec_id: Optional[str] = None
    drawing_rev_id: str; callout_id: Optional[str] = None

class AuditRow(BaseModel):
    triple_id: str
    status: Literal["PASS", "FAIL", "AGENT"]
    parameter: str
    contract_value: str; spec_value: str; drawing_value: str
    check_type: str
    rule: str; explanation: str
    clause_text: str; spec_text: str; drawing_text: str
