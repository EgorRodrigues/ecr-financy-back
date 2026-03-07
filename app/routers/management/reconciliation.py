from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services.ofx_service import OFXService
from app.schemas.reconciliation import OFXImportResponse
from app.dependencies import get_db

router = APIRouter()


@router.post("/import-ofx", response_model=OFXImportResponse)
async def import_ofx(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".ofx"):
        raise HTTPException(status_code=400, detail="Somente arquivos .ofx são permitidos")

    try:
        content = await file.read()
        import io
        service = OFXService(db)
        return service.parse_and_save_ofx(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo OFX: {str(e)}")
