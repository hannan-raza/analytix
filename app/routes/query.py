from fastapi import APIRouter, Depends, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.deps import get_current_user
from app.query.intent_parser import parse_question
from app.query.planner import plan
from app.query.executor import execute
from app.query.formatter import format_response
from app.query.exceptions import PipelineError
from app.schemas.query import QueryRequest
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/query", tags=["AI Query"])


@router.post("/")
def query_ai(
    req: QueryRequest = Body(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    try:
        intent = parse_question(req.question)
        query_plan = plan(intent)
        result = execute(query_plan, db, user_id=user_id)
        answer = format_response(result)

        logger.info("Answer: %r", answer)

        return {
            "intent": intent,
            "data": result,
            "answer": answer,
        }

    except PipelineError as e:
        logger.warning("Pipeline error [%s]: %s", e.stage, e.message)
        return JSONResponse(
            status_code=422,
            content={"error": True, "message": e.message, "stage": e.stage},
        )
    except Exception as e:
        logger.error("Unhandled error in /query: %s", e)
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "An unexpected error occurred. Please try again.",
                "stage": "unknown",
            },
        )
