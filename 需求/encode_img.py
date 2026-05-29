import base64
with open("参考.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
print(b64)
