from pydantic import BaseModel, Field, RootModel


class WBProductData(BaseModel):
    """Схема данных конкретного товара из API Wildberries."""

    nm_id: int = Field(..., alias="nmId", description="Артикул Wildberries")
    price: int = Field(..., description="Текущая цена в копейках/рублях")
    discount: int = Field(..., description="Скидка в процентах")
    promo_code_sum: int = Field(0, alias="promoCodeSum", description="Сумма промокода")


class WBResponsePayload(BaseModel):
    """Схема внутренней полезной нагрузки ответа."""

    products: list[WBProductData] = Field(default_factory=list)


class WBApiResponse(BaseModel):
    """Корневая схема ответа Wildberries API."""

    data: WBResponsePayload


# Схема для валидации списка токенов, если они запрашиваются списком
WBTokenList = RootModel[list[str]]
