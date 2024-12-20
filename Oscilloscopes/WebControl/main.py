from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import os
import requests
from typing import Optional

class ConnectRequest(BaseModel):
    ip: str
    port: int = 8080

class SCPICommand(BaseModel):
    command: str

class OscilloscopeConnection:
    def __init__(self, url: str, port: int):
        self.url = url
        self.port = port
        self.base_url = f"http://{url}:{port}/scpi"

class OscilloscopeManager:
    def __init__(self):
        self._connection: Optional[OscilloscopeConnection] = None
    
    @property
    def is_connected(self) -> bool:
        return self._connection is not None
    
    def connect(self, ip: str, port: int) -> dict:
        """Establish connection to the oscilloscope"""
        try:
            # Test basic connection first
            test_url = f"http://{ip}:{port}/scpi"
            print(f"Testing connection to {test_url}")
            test_response = requests.post(test_url, json="*IDN?")
            print(f"Test response status: {test_response.status_code}")
            print(f"Test response content: {test_response.text}")
            
            self._connection = OscilloscopeConnection(ip, port)
            return {"status": "success", "message": "Connected to oscilloscope"}
        except requests.exceptions.RequestException as e:
            error_msg = f"Connection error: {str(e)}"
            print(error_msg)
            return {"status": "error", "message": error_msg}
        except Exception as e:
            error_msg = f"General error: {str(e)}"
            print(error_msg)
            return {"status": "error", "message": error_msg}
    
    def disconnect(self) -> dict:
        """Disconnect from the oscilloscope"""
        self._connection = None
        return {"status": "success", "message": "Disconnected from oscilloscope"}
    
    def send_command(self, command: str) -> dict:
        """Send SCPI command to the oscilloscope"""
        if not self.is_connected:
            return {"status": "error", "message": "Not connected to oscilloscope"}
        
        try:
            url = f"http://{self._connection.url}:{self._connection.port}/scpi"
            response = requests.post(url, json=command)
            
            # For query commands (ending with ?), we expect a response
            if command.strip().endswith('?'):
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"status": "error", "message": f"Error querying oscilloscope: {response.status_code}"}
            else:
                # For set commands, a 500 status is normal (no response)
                if response.status_code in [200, 500]:
                    return {"status": "success"}
                else:
                    return {"status": "error", "message": f"Error setting oscilloscope parameter: {response.status_code}"}
                    
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Error communicating with oscilloscope: {str(e)}"}

# Create FastAPI app and oscilloscope manager
app = FastAPI()
manager = OscilloscopeManager()

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/connect")
async def connect(request: ConnectRequest):
    return manager.connect(request.ip, request.port)

@app.post("/proxy_scpi")
async def proxy_scpi(command: SCPICommand):
    return manager.send_command(command.command)

@app.post("/disconnect")
async def disconnect():
    return manager.disconnect()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
