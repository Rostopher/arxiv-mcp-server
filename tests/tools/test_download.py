"""Tests for paper download functionality."""

import pytest
import json
from pathlib import Path
from arxiv_mcp_server.tools.download import (
    handle_download,
    get_paper_path,
)


@pytest.mark.asyncio
async def test_download_paper(mocker, temp_storage_path):
    """Test downloading a paper as PDF."""
    paper_id = "2103.12345"

    # Mock arxiv client and PDF download
    mock_paper = mocker.MagicMock()
    mock_paper.download_pdf = mocker.MagicMock()
    mocker.patch("arxiv.Client.results", return_value=iter([mock_paper]))

    response = await handle_download({"paper_id": paper_id})
    status = json.loads(response[0].text)
    assert status["status"] == "success"
    assert status["paper_id"] == paper_id
    assert "pdf_path" in status
    assert status["pdf_path"].endswith(".pdf")


@pytest.mark.asyncio
async def test_download_paper_with_custom_dir(mocker, temp_storage_path):
    """Test downloading a paper to a custom directory."""
    paper_id = "2103.12345"
    custom_dir = str(temp_storage_path / "custom_pdfs")

    # Mock arxiv client and PDF download
    mock_paper = mocker.MagicMock()
    mock_paper.download_pdf = mocker.MagicMock()
    mocker.patch("arxiv.Client.results", return_value=iter([mock_paper]))

    response = await handle_download({
        "paper_id": paper_id,
        "download_dir": custom_dir
    })
    status = json.loads(response[0].text)
    assert status["status"] == "success"
    assert custom_dir in status["pdf_path"]


@pytest.mark.asyncio
async def test_download_existing_paper(temp_storage_path):
    """Test downloading a paper that's already available."""
    paper_id = "2103.12345"
    pdf_path = get_paper_path(paper_id)

    # Create test PDF file
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_text("%PDF-1.4 test")

    response = await handle_download({"paper_id": paper_id})
    status = json.loads(response[0].text)
    assert status["status"] == "success"
    assert "already exists" in status["message"]


@pytest.mark.asyncio
async def test_download_nonexistent_paper(mocker):
    """Test downloading a paper that doesn't exist."""
    mocker.patch("arxiv.Client.results", side_effect=StopIteration())

    response = await handle_download({"paper_id": "invalid.12345"})
    status = json.loads(response[0].text)
    assert status["status"] == "error"
    assert "not found on arXiv" in status["message"]


@pytest.mark.asyncio
async def test_get_paper_path_default(temp_storage_path, mocker):
    """Test get_paper_path uses default storage path."""
    paper_id = "2103.12345"
    path = get_paper_path(paper_id)
    assert path.suffix == ".pdf"
    assert path.stem == paper_id


@pytest.mark.asyncio
async def test_get_paper_path_custom_dir(temp_storage_path, mocker):
    """Test get_paper_path with custom directory."""
    paper_id = "2103.12345"
    custom_dir = "/custom/download/path"
    path = get_paper_path(paper_id, custom_dir)
    assert path.suffix == ".pdf"
    assert path.stem == paper_id
    assert str(path).startswith(custom_dir)
