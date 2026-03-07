from fastapi import APIRouter, File, UploadFile, HTTPException
from app.services.ofx_service import OFXService
from app.schemas.reconciliation import OFXImportResponse

router = APIRouter()


@router.post("/import-ofx", response_model=OFXImportResponse)
async def import_ofx(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".ofx"):
        raise HTTPException(status_code=400, detail="Somente arquivos .ofx são permitidos")

    try:
        content = await file.read()
        import io
        return OFXService.parse_ofx(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo OFX: {str(e)}")
