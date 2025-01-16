from tempfile import NamedTemporaryFile


async def get_temp_file():
    with NamedTemporaryFile(delete=False) as tmp_file:
        yield tmp_file


def format_report(report: list[int | str]) -> dict[str, int | str]:
    return {
        "id": report[0],
        "dynamic": report[1],
        "code": report[2],
        "type_in": report[3],
        "type_out": report[4],
        "timestamp": report[5]
    }
