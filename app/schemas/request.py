from pydantic import BaseModel, Field


class OrderDetails(BaseModel):
    amount: float = Field(..., gt=0.0, description="Transaction amount must be strictly greater than 0")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code, e.g., USD")
    item_category: str = Field(..., min_length=1, description="Category of goods purchased")


class UserAccountDetails(BaseModel):
    account_age_days: int = Field(..., ge=0, description="Account age in days")
    failed_login_attempts_24h: int = Field(..., ge=0, description="Failed login count in past 24 hours")
    past_chargebacks_count: int = Field(..., ge=0, description="Total historical chargebacks")


class DeviceContextDetails(BaseModel):
    ip_address: str = Field(..., description="IPv4 or IPv6 address")
    is_vpn_or_proxy: bool = Field(..., description="Whether traffic routes through VPN/proxy")
    device_fingerprint_hash: str = Field(..., min_length=8, description="Hardware/browser fingerprint token")


class LocationDetails(BaseModel):
    billing_country: str = Field(..., min_length=2, max_length=2, description="2-letter ISO country code")
    shipping_country: str = Field(..., min_length=2, max_length=2, description="2-letter ISO country code")


class TransactionAssessmentRequest(BaseModel):
    transaction_id: str = Field(..., min_length=1, description="Unique transaction identifier")
    order: OrderDetails
    user_account: UserAccountDetails
    device_context: DeviceContextDetails
    location: LocationDetails