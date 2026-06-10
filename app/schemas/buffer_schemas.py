from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


PushType = Literal["marriage", "complain", "compare", "health", "control", "work", "other"]
Probability = Literal["high", "medium", "low"]
ShieldType = Literal["transfer", "boundary", "echo"]
ShareStyle = Literal["safe", "heart", "mini"]


class Shield(BaseModel):
    text: str
    anchor: str


class PushPrediction(BaseModel):
    scene: str
    type: PushType
    probability: Probability
    reason: str
    shields: Dict[ShieldType, Shield]


class GeneratePrepRequest(BaseModel):
    dread: int = Field(default=5, ge=1, le=10)
    lastCallTopics: Optional[str] = None
    fatherType: List[str] = Field(default_factory=lambda: ["push", "complain", "compare"])
    maritalStatus: str = "single"
    age: int = Field(default=28, ge=12, le=100)


class GeneratePrepResponse(BaseModel):
    weekId: str
    energyMode: str
    predictions: List[PushPrediction]
    selectedShields: List[str] = []
    energySupply: str


class TranslateShareRequest(BaseModel):
    rawText: str = Field(..., min_length=1, max_length=300)
    style: ShareStyle = "safe"


class ShareVersion(BaseModel):
    text: str
    parentReaction: str
    replyAdvice: str


class TranslateShareResponse(BaseModel):
    versions: Dict[ShareStyle, ShareVersion]
    selected: ShareVersion


class EmergencyShieldRequest(BaseModel):
    fatherText: str = Field(..., min_length=1, max_length=200)


class EmergencyResponse(BaseModel):
    type: ShieldType
    text: str


class EmergencyShieldResponse(BaseModel):
    detectedType: PushType
    confidence: float = Field(..., ge=0, le=1)
    responses: List[EmergencyResponse]
    reminder: str


class SaveCallLogRequest(BaseModel):
    weekId: str
    dreadAfter: int = Field(..., ge=1, le=10)
    pushCount: int = Field(default=0, ge=0)
    shieldUsed: bool = False
    shieldEffective: bool = False
    notes: str = Field(default="", max_length=500)
