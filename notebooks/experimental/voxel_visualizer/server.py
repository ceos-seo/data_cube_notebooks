import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import pathlib

app = FastAPI()

app.add_middleware(CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"],
    allow_credentials = True)


mountable = [["/static", "./"]]

for api_route, directory_path in mountable:
    print("")

    directory_path = pathlib.Path(directory_path).resolve()

    print(f"Mounting:{directory_path} on {api_route}")
    app.mount(api_route, StaticFiles(directory=directory_path), name= "static")

    for x in directory_path.glob("./*"):
        print(":::",x)
        
print('port:', os.environ['VOXEL_VISUALIZER_PORT'])

uvicorn.run(app,
            port = os.environ['VOXEL_VISUALIZER_PORT'],
            host = "0.0.0.0"
            )

