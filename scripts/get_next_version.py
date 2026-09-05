import sys, json

try:
    data = json.load(sys.stdin)
    for r in data:
        tag = r.get("tagName", "")
        if tag.startswith("alpha-1.00."):
            num = int(tag.split(".")[-1])
            print(f"alpha-1.00.{num + 1:03d}")
            break
    else:
        print("alpha-1.00.001")
except Exception:
    print("alpha-1.00.001")
