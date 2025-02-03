from fastapi import Request

from src.api.presenters import SuccessJSON
from src.common.enums import Operation
from src.common.params import RetrieveData
from src.core.config import LOG
from src.repository import ReportRepository


async def dynamic_reports(request: Request, dynamic: str) -> SuccessJSON:
    reports = ReportRepository.get_dynamic_reports(dynamic)
    LOG.info(f"Found {len(reports)} for dynamic {dynamic}")

    return SuccessJSON(
        request,
        f"Found {len(reports)} for dynamic {dynamic}",
        {
            "dynamic": dynamic,
            "count": len(reports),
            "reports": reports,
        },
    )


async def file_report(
    request: Request, dynamic: str, query: RetrieveData
) -> SuccessJSON:
    report = ReportRepository.get_file_report(dynamic, query)
    LOG.info(f"{query.code} {query.type.value} file report found")

    return SuccessJSON(
        request,
        f"{query.code} {query.type.value} operation reports found",
        {
            "dynamic": dynamic,
            "code": query.code,
            "type": query.type.value,
            "report": report,
        },
    )


async def operation_reports(
    request: Request, dynamic: str, operation: Operation
) -> SuccessJSON:
    reports = ReportRepository.get_operation_reports(dynamic, operation)
    LOG.info(f"{operation.value} operation reports found")

    return SuccessJSON(
        request,
        f"{operation.value} operation reports found",
        {
            "dynamic": dynamic,
            "count": len(reports),
            "reports": reports,
        },
    )
