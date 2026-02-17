"""Download functionality for the arXiv MCP server."""

import arxiv
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import mcp.types as types
from ..config import Settings
import logging

logger = logging.getLogger("arxiv-mcp-server")
settings = Settings()

download_tool = types.Tool(
    name="download_paper",
    description="Download a paper (PDF) from arXiv",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "The arXiv ID of the paper to download",
            },
            "download_dir": {
                "type": "string",
                "description": "Optional: Directory to save the PDF file. If not provided, defaults to the storage path configured in settings.",
            },
        },
        "required": ["paper_id"],
    },
)


def get_paper_path(paper_id: str, custom_dir: Optional[str] = None) -> Path:
    """Get the absolute file path for a paper PDF.

    Args:
        paper_id: The arXiv paper ID
        custom_dir: Optional custom directory to save the PDF. If None, uses default storage path.

    Returns:
        Path to the PDF file
    """
    if custom_dir:
        storage_path = Path(custom_dir)
    else:
        storage_path = Path(settings.STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path / f"{paper_id}.pdf"


async def handle_download(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle paper PDF download requests.

    Downloads a paper from arXiv and saves it as a PDF file.

    Args:
        arguments: Dict containing:
            - paper_id: The arXiv ID of the paper
            - download_dir: Optional custom directory for the PDF

    Returns:
        List of TextContent with download status and file path
    """
    try:
        paper_id = arguments["paper_id"]
        custom_dir = arguments.get("download_dir")

        # Get the PDF path (supports custom download directory)
        pdf_path = get_paper_path(paper_id, custom_dir)

        # Check if paper already exists
        if pdf_path.exists():
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": "success",
                            "message": "Paper PDF already exists",
                            "paper_id": paper_id,
                            "pdf_path": str(pdf_path),
                            "pdf_uri": f"file://{pdf_path}",
                        }
                    ),
                )
            ]

        # Download PDF from arXiv
        client = arxiv.Client()
        paper = next(client.results(arxiv.Search(id_list=[paper_id])))
        paper.download_pdf(dirpath=pdf_path.parent, filename=pdf_path.name)

        logger.info(f"Downloaded paper {paper_id} to {pdf_path}")

        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "status": "success",
                        "message": "Paper PDF downloaded successfully",
                        "paper_id": paper_id,
                        "pdf_path": str(pdf_path),
                        "pdf_uri": f"file://{pdf_path}",
                    }
                ),
            )
        ]

    except StopIteration:
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "status": "error",
                        "message": f"Paper {paper_id} not found on arXiv",
                    }
                ),
            )
        ]
    except Exception as e:
        logger.error(f"Download error for {paper_id}: {str(e)}")
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": f"Error: {str(e)}"}),
            )
        ]
