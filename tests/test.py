import asyncio, json, tempfile
from arxiv_mcp_server.tools.search import handle_search
from arxiv_mcp_server.tools.download import handle_download

async def main():
    res1 = await handle_search({
        "query": 'ti:"attention is all you need"',
        "max_results": 3,
        "sort_by": "relevance",
    })
    print("SEARCH 1:", res1[0].text[:500])

    res2 = await handle_search({
        "query": "transformer",
        "max_results": 3,
        "categories": ["cs.CL"],
        "date_from": "2017-01-01",
        "date_to": "2018-12-31",
        "sort_by": "date",
    })
    print("SEARCH 2:", res2[0].text[:500])

    # 如果 search1 成功，就尝试下载第一个结果
    data1 = json.loads(res1[0].text)
    if data1.get("papers"):
        paper_id = data1["papers"][0]["id"]
        with tempfile.TemporaryDirectory() as tmpdir:
            res3 = await handle_download({"paper_id": paper_id, "download_dir": tmpdir})
            print("DOWNLOAD:", res3[0].text)

asyncio.run(main())