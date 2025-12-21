from app.models.accounts import AccountOut
from uuid import uuid4
from datetime import datetime

def test_masking():
    data = {
        "id": uuid4(),
        "name": "Test Account",
        "type": "credit_card",
        "card_number": "1234567812345678",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "active": True
    }
    
    account = AccountOut(**data)
    print(f"Original: {data['card_number']}")
    print(f"Masked: {account.card_number}")
    assert account.card_number == "**** **** **** 5678"

    data_short = {
        "id": uuid4(),
        "name": "Test Account Short",
        "type": "credit_card",
        "card_number": "123",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "active": True
    }
    account_short = AccountOut(**data_short)
    print(f"Short Original: {data_short['card_number']}")
    print(f"Short Masked: {account_short.card_number}")
    # Based on my logic: if len < 4, it returns as is? 
    # Wait, my logic was: if v and len(v) >= 4. So "123" will be returned as "123".
    
    data_none = {
        "id": uuid4(),
        "name": "Test Account None",
        "type": "credit_card",
        "card_number": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "active": True
    }
    account_none = AccountOut(**data_none)
    print(f"None Original: {data_none['card_number']}")
    print(f"None Masked: {account_none.card_number}")
    assert account_none.card_number is None

if __name__ == "__main__":
    test_masking()