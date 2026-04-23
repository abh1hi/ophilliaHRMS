from fastapi import FastAPI, Depends

def dep1():
    return "dep1"

def dep2(d: str = Depends(dep1)):
    return f"dep2-{d}"

app = FastAPI()

@app.get("/")
def read_root(d: str = Depends(dep2)):
    return {"Hello": d}
