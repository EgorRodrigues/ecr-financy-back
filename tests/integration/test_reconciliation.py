import io
from fastapi.testclient import TestClient
from app.main import app
import pytest

def test_import_ofx(client: TestClient):
    ofx_content = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE
<OFX>
<SIGNONMSGSRSV1>
<SONRS>
<STATUS>
<CODE>0
<SEVERITY>INFO
</STATUS>
<DTSERVER>20231027120000
<LANGUAGE>POR
</SONRS>
</SIGNONMSGSRSV1>
<BANKMSGSRSV1>
<STMTTRNRS>
<TRNUID>1
<STATUS>
<CODE>0
<SEVERITY>INFO
</STATUS>
<STMTRS>
<CURDEF>BRL
<BANKACCTFROM>
<BANKID>033
<ACCTID>123456789
<ACCTTYPE>CHECKING
</BANKACCTFROM>
<BANKTRANLIST>
<DTSTART>20231001120000
<DTEND>20231027120000
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20231015120000
<TRNAMT>-100.00
<FITID>12345
<MEMO>TEST DEBIT
</STMTTRN>
<STMTTRN>
<TRNTYPE>CREDIT
<DTPOSTED>20231016120000
<TRNAMT>200.00
<FITID>12346
<MEMO>TEST CREDIT
</STMTTRN>
</BANKTRANLIST>
<LEDGERBAL>
<BALAMT>1000.00
<DTASOF>20231027120000
</LEDGERBAL>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>
"""
    file = ("test.ofx", ofx_content.encode("utf-8"), "application/x-ofx")
    response = client.post("/reconciliation/import-ofx", files={"file": file})
    
    if response.status_code != 200:
        print(f"Error Response: {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["transactions"]) == 2
    assert data["transactions"][0]["amount"] == -100.0
    assert data["transactions"][0]["memo"] == "TEST DEBIT"
    assert data["transactions"][1]["amount"] == 200.0
    assert data["transactions"][1]["memo"] == "TEST CREDIT"
    assert data["transactions"][0]["bank_id"] == "033"
    assert data["account_id"] == "123456789"
    assert data["balance"] == 1000.0


def test_deactivate_ofx_transaction(client: TestClient):
    # 1. Importar OFX
    ofx_content = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE
<OFX>
<SIGNONMSGSRSV1>
<SONRS>
<STATUS>
<CODE>0
<SEVERITY>INFO
</STATUS>
<DTSERVER>20231027120000
<LANGUAGE>POR
</SONRS>
</SIGNONMSGSRSV1>
<BANKMSGSRSV1>
<STMTTRNRS>
<TRNUID>1
<STATUS>
<CODE>0
<SEVERITY>INFO
</STATUS>
<STMTRS>
<CURDEF>BRL
<BANKACCTFROM>
<BANKID>033
<ACCTID>123456789
<ACCTTYPE>CHECKING
</BANKACCTFROM>
<BANKTRANLIST>
<DTSTART>20231001120000
<DTEND>20231027120000
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20231015120000
<TRNAMT>-100.00
<FITID>99999
<MEMO>DEACTIVATE TEST
</STMTTRN>
</BANKTRANLIST>
<LEDGERBAL>
<BALAMT>1000.00
<DTASOF>20231027120000
</LEDGERBAL>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>
"""
    file = ("test.ofx", ofx_content.encode("utf-8"), "application/x-ofx")
    client.post("/reconciliation/import-ofx", files={"file": file})

    # 2. Buscar transações não reconciliadas
    response = client.get("/reconciliation/unreconciled-ofx-transactions")
    assert response.status_code == 200
    transactions = response.json()
    
    # Encontrar a transação que acabamos de importar
    tx = next(t for t in transactions if t["fitid"] == "99999")
    tx_id = tx["id"]

    # 3. Desativar a transação
    response = client.patch(f"/reconciliation/ofx-transactions/{tx_id}/deactivate")
    assert response.status_code == 200
    assert response.json()["message"] == "Transação OFX desativada com sucesso"

    # 4. Buscar novamente e garantir que ela não apareça
    response = client.get("/reconciliation/unreconciled-ofx-transactions")
    assert response.status_code == 200
    transactions = response.json()
    assert not any(t["id"] == tx_id for t in transactions)
