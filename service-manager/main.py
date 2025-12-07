import asyncio
import os
import subprocess
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates

template_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=template_dir)

managed_services = [
    service.strip() for service in os.environ.get("SM_SERVICES", "").split()
]

root_path = os.environ.get("SM_ROOT", "")
assert not root_path.endswith("/")


app = FastAPI(root_path=root_path)


@app.post("/service/{service}/status")
async def service_status(service: str):
    if service not in managed_services:
        return Response(status_code=404)
    cmd = f"systemctl is-active {service}"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    body = result.stdout.strip()
    status_code = 200 if body == "active" else 500
    return PlainTextResponse(body, status_code=status_code)


@app.post("/service/{service}/restart")
async def restart_service(service: str):
    if service not in managed_services:
        return Response(status_code=404)
    cmd = f"systemctl restart {service}"
    subprocess.Popen(cmd.split())
    return Response(status_code=202)


@app.post("/service/{service}/stop")
async def stop_service(service: str):
    if service not in managed_services:
        return Response(status_code=404)
    cmd = f"systemctl stop {service}"
    subprocess.Popen(cmd.split())
    return Response(status_code=202)


@app.post("/service/{service}/start")
async def start_service(service: str):
    if service not in managed_services:
        return Response(status_code=404)
    cmd = f"systemctl start {service}"
    subprocess.Popen(cmd.split())
    return Response(status_code=202)


@app.post("/service/{service}/reload")
async def reload_service(service: str):
    if service not in managed_services:
        return Response(status_code=404)
    cmd = f"systemctl reload {service}; systemctl restart {service}"
    subprocess.Popen(cmd, shell=True)
    return Response(status_code=202)


async def stream_journalctl(service: str):
    process = await asyncio.create_subprocess_exec(
        "journalctl",
        "-fu",
        service,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        while True:
            line = await process.stdout.readline()
            print(line)
            if not line:
                break
            yield line.decode("utf-8")
    except asyncio.CancelledError:
        process.terminate()
        await process.wait()
    finally:
        if process.returncode is None:
            process.terminate()
            await process.wait()


@app.get("/service/{service}/logs")
async def stream_logs(service: str):
    if service not in managed_services:
        return Response(status_code=404)
    return StreamingResponse(stream_journalctl(service), media_type="text/plain")


@app.get("/")
async def ui(request: Request):
    context = {
        "managed_services": managed_services,
        "request": request,
        "root_path": root_path,
    }
    return templates.TemplateResponse("index.html", context=context)


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
