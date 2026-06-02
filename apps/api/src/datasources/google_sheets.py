"""Google Sheets API client."""
import logging
from typing import Optional
import httpx

from src.datasources.oauth import refresh_google_token
from src.exceptions import GoogleSheetsError

logger = logging.getLogger("deskforge.datasources.google_sheets")


async def fetch_sheet_data(
    access_token: str,
    spreadsheet_id: str,
    tab_name: Optional[str] = None,
) -> dict:
    """Fetch data from a Google Sheet."""
    range_str = tab_name if tab_name else "Sheet1"
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_str}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                params={"valueRenderOption": "UNFORMATTED_VALUE"},
            )
            if response.status_code != 200:
                raise GoogleSheetsError(f"Failed to fetch sheet: {response.text}")

            data = response.json()
            values = data.get("values", [])
            if not values:
                return {"columns": [], "rows": [], "row_count": 0}

            # First row is headers
            headers = values[0]
            rows = []
            for row in values[1:]:
                row_data = {}
                for i, header in enumerate(headers):
                    row_data[header] = row[i] if i < len(row) else None
                rows.append(row_data)

            return {
                "columns": headers,
                "rows": rows,
                "row_count": len(rows),
            }

        except httpx.HTTPError as e:
            raise GoogleSheetsError(f"Network error: {e}")


async def get_spreadsheet_metadata(access_token: str, spreadsheet_id: str) -> dict:
    """Get spreadsheet metadata including tab names."""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                params={"fields": "sheets.properties"},
            )
            if response.status_code != 200:
                raise GoogleSheetsError(f"Failed to get metadata: {response.text}")

            data = response.json()
            sheets = data.get("sheets", [])
            tabs = [s["properties"]["title"] for s in sheets]
            return {"tabs": tabs}

        except httpx.HTTPError as e:
            raise GoogleSheetsError(f"Network error: {e}")


async def write_to_sheet(
    access_token: str,
    spreadsheet_id: str,
    tab_name: str,
    range_str: str,
    values: list[list],
) -> None:
    """Write data to a Google Sheet."""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{tab_name}!{range_str}"
    url += "?valueInputOption=USER_ENTERED"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.put(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={"values": values},
            )
            if response.status_code != 200:
                raise GoogleSheetsError(f"Failed to write: {response.text}")

        except httpx.HTTPError as e:
            raise GoogleSheetsError(f"Network error: {e}")


def extract_spreadsheet_id(url: str) -> Optional[str]:
    """Extract spreadsheet ID from a Google Sheets URL."""
    import re
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else None
