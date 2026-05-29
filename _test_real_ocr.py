import sys, time
sys.stdout.reconfigure(encoding='utf-8')
try:
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_textline_orientation=True, device='cpu')
    t0 = time.time()
    for page in ocr.predict(r"D:\data\aatomcode\jinrong-sdd\需求\参考.png"):
        texts = page.get('rec_texts') or []
        scores = page.get('rec_scores') or []
        polys = page.get('rec_polys') or []
        print(f"blocks={len(texts)} time={time.time()-t0:.1f}s")
        for t, s in zip(texts[:5], scores[:5]):
            print(f"  [{s:.2f}] {t}")
        break
    print("SUCCESS")
except Exception as e:
    import traceback; traceback.print_exc()
