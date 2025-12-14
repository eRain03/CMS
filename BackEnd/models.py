from pydantic import BaseModel
from typing import List, Optional

# Farmer: 必须精确到城市
class FarmerCreate(BaseModel):
    race: str
    age: int
    sex: str
    quantity: int
    state: str       # 例如 "PA"
    city: str        # 例如 "Santarém"
    contact: str

class Farmer(FarmerCreate):
    id: str
    timestamp: float
    owner_id: Optional[str] = None

# 辅助模型：Buyer 的目标区域
class TargetRegion(BaseModel):
    state: str       # "PA"
    city: str        # "Santarém" 或 "ANY" (代表全州)

# Buyer: location 变成目标区域列表
class BuyerCreate(BaseModel):
    targets: List[TargetRegion] # 核心变化：不再是简单的字符串列表
    race: str
    ageMin: Optional[int] = 0
    ageMax: Optional[int] = 100
    sex: str
    quantity: int
    contact: str

class Buyer(BuyerCreate):
    id: str
    timestamp: float
    owner_id: Optional[str] = None